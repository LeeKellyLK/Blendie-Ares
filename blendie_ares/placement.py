import math
import random

from mathutils import Matrix, Vector

from .sampling import matrix_from_normal_tangent


def _rotation_jitter_matrix(rng, deg):
    if deg <= 1e-8:
        return Matrix.Identity(4)
    angle = math.radians(rng.uniform(-deg, deg))
    return Matrix.Rotation(angle, 4, "Z")


def _scale_jitter(rng, amount):
    if amount <= 1e-8:
        return 1.0
    return max(0.001, 1.0 + rng.uniform(-amount, amount))


def _make_transform(sample, rng, settings):
    base = matrix_from_normal_tangent(sample["point"], sample["normal"], sample["tangent"])
    transform = base @ _rotation_jitter_matrix(rng, settings.rotation_jitter_deg)
    scale_factor = _scale_jitter(rng, settings.scale_jitter)
    transform = transform @ Matrix.Scale(scale_factor, 4)
    return transform


def _chain_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    points = [s["point"] for s in samples]
    mins = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maxs = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    extent = maxs - mins
    axis = max(range(3), key=lambda i: extent[i])

    ordered = sorted(samples, key=lambda s: s["point"][axis])
    spacing = max(1e-5, settings.spacing * (1.0 - settings.contact_tolerance * 0.75))

    selected = []
    previous = None
    for sample in ordered:
        if previous is None or (sample["point"] - previous["point"]).length >= spacing:
            selected.append(sample)
            previous = sample
        if len(selected) >= max_instances:
            break
    return selected


def _fill_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    candidates = list(samples)
    rng.shuffle(candidates)
    min_dist = max(1e-5, settings.spacing * (1.0 - settings.contact_tolerance))
    target_dist = max(min_dist, settings.spacing)

    selected = []
    tries = 0
    idx = 0
    while (
        idx < len(candidates)
        and len(selected) < max_instances
        and tries < settings.max_iterations
    ):
        sample = candidates[idx]
        idx += 1
        tries += 1

        if not selected:
            selected.append(sample)
            continue

        nearest = min(selected, key=lambda s: (sample["point"] - s["point"]).length)
        nearest_dist = (sample["point"] - nearest["point"]).length
        if nearest_dist < min_dist:
            continue

        if nearest_dist > target_dist * (1.0 + settings.contact_tolerance):
            direction = (sample["point"] - nearest["point"])
            if direction.length > 1e-8:
                direction.normalize()
                sample = sample.copy()
                sample["point"] = nearest["point"] + direction * target_dist

        selected.append(sample)

    return selected


def _guided_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    step = max(1, int(round(1.0 / max(0.01, settings.density))))
    selected = samples[::step]
    if len(selected) > max_instances:
        selected = selected[:max_instances]
    return selected


def select_samples_for_mode(samples, settings, max_instances=None):
    rng = random.Random(settings.random_seed)
    max_instances = max_instances if max_instances is not None else settings.max_instances
    if settings.mode == "CHAIN":
        return _chain_mode(samples, settings, rng, max_instances)
    if settings.mode == "FILL":
        return _fill_mode(samples, settings, rng, max_instances)
    return _guided_mode(samples, settings, rng, max_instances)


def generate_transforms(samples, settings, max_instances=None):
    rng = random.Random(settings.random_seed + 17)
    selected = select_samples_for_mode(samples, settings, max_instances=max_instances)
    return [_make_transform(sample, rng, settings) for sample in selected]
