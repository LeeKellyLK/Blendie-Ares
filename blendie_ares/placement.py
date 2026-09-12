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


def _surface_chart(sample):
    normal = sample["normal"]
    normal_axis = max(range(3), key=lambda axis: abs(normal[axis]))
    surface_axes = [axis for axis in range(3) if axis != normal_axis]
    return (normal_axis, normal[normal_axis] < 0.0), surface_axes[0], surface_axes[1]


def _chain_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    spacing = max(1e-5, settings.spacing * max(0.1, 1.0 - settings.contact_tolerance * 0.5))
    row_step = max(1e-5, spacing * 0.8660254)

    charts = {}
    for sample in samples:
        chart_key, u_axis, v_axis = _surface_chart(sample)
        chart = charts.setdefault(chart_key, (u_axis, v_axis, []))
        chart[2].append(sample)

    rows = {}
    for chart_key, (u_axis, v_axis, chart_samples) in charts.items():
        min_u = min(sample["point"][u_axis] for sample in chart_samples)
        min_v = min(sample["point"][v_axis] for sample in chart_samples)
        buckets = {}
        for sample in chart_samples:
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

        for (row, col), (_, sample) in buckets.items():
            rows.setdefault((chart_key, row), []).append((col, sample, u_axis))

    selected = []
    for (_, row), row_items in sorted(rows.items()):
        row_items = sorted(row_items, key=lambda item: item[0], reverse=bool(row % 2))
        for _, sample, u_axis in row_items:
            sample = sample.copy()
            u_direction = Vector((0.0, 0.0, 0.0))
            u_direction[u_axis] = 1.0
            tangent = u_direction - sample["normal"] * u_direction.dot(sample["normal"])
            if tangent.length <= 1e-8:
                tangent = sample["tangent"].copy()
            tangent.normalize()
            if row % 2:
                alt_tangent = sample["normal"].cross(tangent)
                if alt_tangent.length > 1e-8:
                    alt_tangent.normalize()
                    tangent = alt_tangent
            sample["tangent"] = tangent
            selected.append(sample)

    if len(selected) > max_instances:
        step = len(selected) / max_instances
        return [selected[int(index * step)] for index in range(max_instances)]
    return selected


def _fill_mode(samples, settings, rng, max_instances):
    if not samples:
        return []

    candidates = list(samples)
    rng.shuffle(candidates)
    min_dist = max(1e-5, settings.spacing * (1.0 - settings.contact_tolerance))
    min_dist_sq = min_dist * min_dist
    neighbor_offsets = [
        (dx, dy, dz)
        for dx in (-1, 0, 1)
        for dy in (-1, 0, 1)
        for dz in (-1, 0, 1)
    ]

    def grid_key(point):
        return (
            int(math.floor(point.x / min_dist)),
            int(math.floor(point.y / min_dist)),
            int(math.floor(point.z / min_dist)),
        )

    selected = []
    grid = {}
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
            grid.setdefault(grid_key(sample["point"]), []).append(sample["point"])
            continue

        point = sample["point"]
        key = grid_key(point)
        too_close = False
        for dx, dy, dz in neighbor_offsets:
            neighbor_key = (key[0] + dx, key[1] + dy, key[2] + dz)
            for neighbor_point in grid.get(neighbor_key, []):
                if (point - neighbor_point).length_squared < min_dist_sq:
                    too_close = True
                    break
            if too_close:
                break

        if too_close:
            continue

        selected.append(sample)
        grid.setdefault(key, []).append(point)

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
