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


def _projection_axes(samples):
    points = [s["point"] for s in samples]
    mins = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    maxs = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    extent = maxs - mins
    ordered = sorted(range(3), key=lambda i: extent[i], reverse=True)
    return ordered[0], ordered[1]


def _chain_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    spacing = max(1e-5, settings.spacing * max(0.1, 1.0 - settings.contact_tolerance * 0.5))
    row_step = max(1e-5, spacing * 0.8660254)
    u_axis, v_axis = _projection_axes(samples)
    min_u = min(s["point"][u_axis] for s in samples)
    min_v = min(s["point"][v_axis] for s in samples)

    buckets = {}
    for sample in samples:
        point = sample["point"]
        local_u = point[u_axis] - min_u
        local_v = point[v_axis] - min_v
        row = int(local_v // row_step)
        row_offset = 0.5 if (row % 2) else 0.0
        col = int((local_u / spacing) - row_offset)

        center_u = (col + row_offset + 0.5) * spacing
        center_v = (row + 0.5) * row_step
        score = (local_u - center_u) ** 2 + (local_v - center_v) ** 2

        key = (row, col)
        current = buckets.get(key)
        if current is None or score < current[0]:
            buckets[key] = (score, sample)

    rows = {}
    for (row, col), (_, sample) in buckets.items():
        rows.setdefault(row, []).append((col, sample))

    selected = []
    for row in sorted(rows):
        row_items = sorted(rows[row], key=lambda x: x[0], reverse=bool(row % 2))
        for _, sample in row_items:
            if row % 2:
                sample = sample.copy()
                alt_tangent = sample["normal"].cross(sample["tangent"])
                if alt_tangent.length > 1e-8:
                    alt_tangent.normalize()
                    sample["tangent"] = alt_tangent
            selected.append(sample)
            if len(selected) >= max_instances:
                return selected
    return selected


def _fill_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    candidates = list(samples)
    rng.shuffle(candidates)
    min_dist = max(1e-5, settings.spacing * (1.0 - settings.contact_tolerance))
    min_dist_sq = min_dist * min_dist
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

        nearest_dist_sq = min((sample["point"] - s["point"]).length_squared for s in selected)
        if nearest_dist_sq < min_dist_sq:
            continue

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
