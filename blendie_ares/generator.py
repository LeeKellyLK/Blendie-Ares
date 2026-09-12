import random
from typing import Iterable, List, Tuple

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree

GEN_MARKER = "blendie_ares_generated"


def validate_mesh_object(obj: bpy.types.Object, label: str):
    if obj is None:
        raise ValueError(f"{label} is not set")
    if obj.type != "MESH":
        raise ValueError(f"{label} must be a mesh object")
    if obj.data is None or len(obj.data.vertices) == 0:
        raise ValueError(f"{label} mesh has no vertices")


def ensure_output_collection(scene: bpy.types.Scene, name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if not any(child == collection for child in scene.collection.children):
        scene.collection.children.link(collection)
    return collection


def clear_generated(collection: bpy.types.Collection):
    for obj in list(collection.objects):
        if obj.get(GEN_MARKER):
            bpy.data.objects.remove(obj, do_unlink=True)


def _duplicate_at(
    source_obj: bpy.types.Object,
    collection: bpy.types.Collection,
    location: Vector,
    rotation_quaternion,
):
    new_obj = source_obj.copy()
    new_obj.data = source_obj.data
    new_obj.location = location
    new_obj.rotation_mode = "QUATERNION"
    new_obj.rotation_quaternion = rotation_quaternion
    new_obj[GEN_MARKER] = True
    collection.objects.link(new_obj)
    return new_obj


def _orientation_from_tangent_normal(tangent: Vector, normal: Vector):
    forward = tangent.normalized()
    up = normal.normalized()
    if abs(forward.dot(up)) > 0.999:
        up = Vector((0.0, 0.0, 1.0))
    right = forward.cross(up).normalized()
    up = right.cross(forward).normalized()
    matrix = Matrix((
        right.to_4d(),
        forward.to_4d(),
        up.to_4d(),
        Vector((0.0, 0.0, 0.0, 1.0)),
    ))
    return matrix.to_3x3().to_quaternion()


def _sample_triangle_point(v0: Vector, v1: Vector, v2: Vector):
    r1 = random.random()
    r2 = random.random()
    sqrt_r1 = r1 ** 0.5
    return (1 - sqrt_r1) * v0 + (sqrt_r1 * (1 - r2)) * v1 + (sqrt_r1 * r2) * v2


def _ordered_edge_loop_vertices(target_obj: bpy.types.Object) -> List[int]:
    if target_obj.mode != "EDIT":
        raise ValueError("Chain Link mode requires target mesh in Edit Mode with selected edge loop")
    bm = bmesh.from_edit_mesh(target_obj.data)
    selected_edges = [e for e in bm.edges if e.select]
    if len(selected_edges) < 1:
        raise ValueError("No selected edges found on target mesh")

    adjacency = {}
    edges = []
    for edge in selected_edges:
        a = edge.verts[0].index
        b = edge.verts[1].index
        edges.append((a, b))
        adjacency.setdefault(a, []).append(b)
        adjacency.setdefault(b, []).append(a)

    bad_degree = [idx for idx, linked in adjacency.items() if len(linked) > 2]
    if bad_degree:
        raise ValueError("Selected edges must form a single edge loop/path (no branching)")

    endpoints = [idx for idx, linked in adjacency.items() if len(linked) == 1]
    if len(endpoints) not in (0, 2):
        raise ValueError("Selected edges must form one continuous path or closed loop")

    start = endpoints[0] if endpoints else min(adjacency.keys())
    ordered = [start]
    visited_edges = set()
    prev = None
    cur = start

    while True:
        next_candidates = [n for n in adjacency[cur] if (min(cur, n), max(cur, n)) not in visited_edges and n != prev]
        if not next_candidates:
            break
        nxt = next_candidates[0]
        visited_edges.add((min(cur, nxt), max(cur, nxt)))
        ordered.append(nxt)
        prev, cur = cur, nxt

    if len(visited_edges) != len(edges):
        raise ValueError("Selected edges must form one connected edge loop/path")

    return ordered


def _polyline_points(vertices: Iterable[Vector], step: float) -> List[Vector]:
    points = list(vertices)
    if len(points) < 2:
        return points
    out = [points[0]]
    carry = 0.0
    for i in range(len(points) - 1):
        a = points[i]
        b = points[i + 1]
        seg = b - a
        length = seg.length
        if length < 1e-9:
            continue
        direction = seg / length
        dist = max(step - carry, 0.0)
        while dist <= length:
            out.append(a + direction * dist)
            dist += step
        carry = max(dist - length, 0.0)
    return out


def generate_surface_fill(
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    collection: bpy.types.Collection,
    spacing: float,
    max_count: int,
    normal_offset: float,
):
    mesh = target_obj.data
    mesh.calc_loop_triangles()
    triangles = mesh.loop_triangles
    if not triangles:
        raise ValueError("Target mesh has no triangles to sample")

    world = target_obj.matrix_world
    normal_matrix = world.to_3x3().inverted().transposed()
    weighted = []
    total_area = 0.0
    for tri in triangles:
        verts = [world @ mesh.vertices[i].co for i in tri.vertices]
        area = (verts[1] - verts[0]).cross(verts[2] - verts[0]).length * 0.5
        if area > 0:
            total_area += area
            weighted.append((total_area, tri, verts))
    if total_area <= 0:
        raise ValueError("Target mesh triangles have zero total area")

    placed_points: List[Vector] = []
    attempts = max_count * 30
    for _ in range(attempts):
        if len(placed_points) >= max_count:
            break
        pick = random.uniform(0.0, total_area)
        tri, verts = None, None
        for cumulative, t, v in weighted:
            if pick <= cumulative:
                tri, verts = t, v
                break
        if tri is None:
            continue

        candidate = _sample_triangle_point(verts[0], verts[1], verts[2])
        if any((candidate - p).length < spacing for p in placed_points):
            continue

        normal = (normal_matrix @ tri.normal).normalized()
        tangent = (verts[1] - verts[0]).normalized()
        rot = _orientation_from_tangent_normal(tangent, normal)
        loc = candidate + normal * normal_offset
        _duplicate_at(source_obj, collection, loc, rot)
        placed_points.append(candidate)


def generate_chain_link(
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    collection: bpy.types.Collection,
    spacing: float,
    normal_offset: float,
    depsgraph,
):
    ordered_indices = _ordered_edge_loop_vertices(target_obj)
    mesh = target_obj.data
    world_points = [target_obj.matrix_world @ mesh.vertices[i].co for i in ordered_indices]
    chain_points = _polyline_points(world_points, spacing)
    if len(chain_points) < 2:
        raise ValueError("Selected edge loop path is too short for generation")

    bvh = BVHTree.FromObject(target_obj, depsgraph)
    if bvh is None:
        raise ValueError("Could not build target mesh spatial data")

    for i, point in enumerate(chain_points):
        prev_idx = max(i - 1, 0)
        next_idx = min(i + 1, len(chain_points) - 1)
        tangent = chain_points[next_idx] - chain_points[prev_idx]
        if tangent.length < 1e-9:
            tangent = Vector((1.0, 0.0, 0.0))

        nearest = bvh.find_nearest(point)
        normal = nearest[2] if nearest else Vector((0.0, 0.0, 1.0))
        rot = _orientation_from_tangent_normal(tangent, normal)
        if i % 2:
            rot = rot @ Quaternion((1.0, 0.0, 0.0), 1.57079632679)
        loc = point + normal.normalized() * normal_offset
        _duplicate_at(source_obj, collection, loc, rot)


def generate(
    depsgraph,
    scene: bpy.types.Scene,
    source_obj: bpy.types.Object,
    target_obj: bpy.types.Object,
    mode: str,
    spacing: float,
    fill_count: int,
    normal_offset: float,
    seed: int,
    output_collection_name: str,
):
    validate_mesh_object(source_obj, "Source object")
    validate_mesh_object(target_obj, "Target object")
    if source_obj == target_obj:
        raise ValueError("Source and target must be different objects")
    if spacing <= 0:
        raise ValueError("Spacing must be greater than zero")

    random.seed(seed)
    collection = ensure_output_collection(scene, output_collection_name)
    clear_generated(collection)

    if mode == "SURFACE_FILL":
        generate_surface_fill(source_obj, target_obj, collection, spacing, fill_count, normal_offset)
    elif mode == "CHAIN_LINK":
        generate_chain_link(source_obj, target_obj, collection, spacing, normal_offset, depsgraph)
    else:
        raise ValueError(f"Unsupported mode: {mode}")


def clear(scene: bpy.types.Scene, output_collection_name: str):
    collection = bpy.data.collections.get(output_collection_name)
    if collection is None:
        return
    clear_generated(collection)
