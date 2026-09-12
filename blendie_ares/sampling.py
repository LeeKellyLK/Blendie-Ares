import random

import bpy
from mathutils import Matrix, Vector


def _triangle_data(target_obj, depsgraph):
    eval_obj = target_obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    mesh.calc_loop_triangles()

    world = eval_obj.matrix_world
    triangles = []
    for tri in mesh.loop_triangles:
        v0 = world @ mesh.vertices[tri.vertices[0]].co
        v1 = world @ mesh.vertices[tri.vertices[1]].co
        v2 = world @ mesh.vertices[tri.vertices[2]].co
        normal = (v1 - v0).cross(v2 - v0)
        area = normal.length * 0.5
        if area <= 1e-10:
            continue
        normal.normalize()
        tangent = (v1 - v0)
        if tangent.length < 1e-8:
            tangent = (v2 - v0)
        if tangent.length > 1e-8:
            tangent.normalize()
        triangles.append((v0, v1, v2, normal, tangent, area))

    eval_obj.to_mesh_clear()
    return triangles


def target_surface_area(target_obj, depsgraph):
    triangles = _triangle_data(target_obj, depsgraph)
    return sum(t[5] for t in triangles)


def _pick_triangle_index(mode, triangles, areas, rng, index):
    if mode == "UNIFORM":
        return index % len(triangles)
    if mode == "RANDOM":
        return rng.randrange(0, len(triangles))
    return rng.choices(range(len(triangles)), weights=areas, k=1)[0]


def _sample_point_on_triangle(v0, v1, v2, rng):
    r1 = rng.random()
    r2 = rng.random()
    s1 = r1 ** 0.5
    a = 1.0 - s1
    b = s1 * (1.0 - r2)
    c = s1 * r2
    return (v0 * a) + (v1 * b) + (v2 * c)


def sample_target_surface(target_obj, count, distribution, seed, depsgraph=None):
    depsgraph = depsgraph or bpy.context.evaluated_depsgraph_get()
    triangles = _triangle_data(target_obj, depsgraph)
    if not triangles:
        return []

    areas = [t[5] for t in triangles]
    rng = random.Random(seed)

    samples = []
    for i in range(count):
        tri_idx = _pick_triangle_index(distribution, triangles, areas, rng, i)
        v0, v1, v2, normal, tangent, _ = triangles[tri_idx]
        point = _sample_point_on_triangle(v0, v1, v2, rng)
        samples.append(
            {
                "point": point,
                "normal": normal.copy(),
                "tangent": tangent.copy(),
            }
        )
    return samples


def matrix_from_normal_tangent(location: Vector, normal: Vector, tangent: Vector):
    z_axis = normal.normalized() if normal.length > 1e-8 else Vector((0.0, 0.0, 1.0))
    x_axis = tangent.normalized() if tangent.length > 1e-8 else Vector((1.0, 0.0, 0.0))

    if abs(x_axis.dot(z_axis)) > 0.999:
        x_axis = Vector((0.0, 1.0, 0.0))

    y_axis = z_axis.cross(x_axis)
    if y_axis.length <= 1e-8:
        y_axis = Vector((0.0, 1.0, 0.0))
    y_axis.normalize()

    x_axis = y_axis.cross(z_axis)
    x_axis.normalize()

    rotation = Matrix((x_axis, y_axis, z_axis)).transposed().to_4x4()
    rotation.translation = location
    return rotation
