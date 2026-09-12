import bpy
import uuid

from .placement import generate_transforms
from .sampling import sample_target_surface, target_surface_area
from .utils import (
    GENERATED_KEY,
    PREVIEW_COLLECTION_NAME,
    RESULT_COLLECTION_NAME,
    clear_collection,
    get_or_create_collection,
    remove_collection,
)
from .validation import validate_configuration


def _scene_owner_id(settings):
    if not settings.scene_uid:
        settings.scene_uid = uuid.uuid4().hex
    return settings.scene_uid


def _scene_collection_name(settings, base_name):
    return f"{base_name}_{_scene_owner_id(settings)}"


def _build_instances(
    context,
    source_obj,
    transforms,
    collection_name,
    owner_id,
    convert_to_real,
    chunk_size,
):
    collection = get_or_create_collection(context.scene, collection_name, owner_id)
    clear_collection(collection, context.scene, owner_id)

    created = []
    for idx, matrix in enumerate(transforms, start=1):
        inst = source_obj.copy()
        inst.data = source_obj.data
        inst.animation_data_clear()
        inst.matrix_world = matrix
        inst[GENERATED_KEY] = True
        collection.objects.link(inst)

        if convert_to_real and inst.type == "MESH" and inst.data is not None:
            inst.data = inst.data.copy()

        created.append(inst)
        if idx % max(1, chunk_size) == 0:
            context.view_layer.update()

    return created


def _compute_transforms_for_targets(context, settings, targets, preview):
    base_count = settings.preview_instances if preview else settings.max_instances
    depsgraph = context.evaluated_depsgraph_get()
    areas = [max(0.0, target_surface_area(target, depsgraph)) for target in targets]
    valid_pairs = [(target, area) for target, area in zip(targets, areas) if area > 1e-10]
    if not valid_pairs:
        return []

    targets = [pair[0] for pair in valid_pairs]
    areas = [pair[1] for pair in valid_pairs]
    total_area = sum(areas)

    if total_area <= 1e-10:
        quotas = [base_count // len(targets) for _ in targets]
        for i in range(base_count % len(targets)):
            quotas[i] += 1
    else:
        positive_indices = [i for i, area in enumerate(areas) if area > 1e-10]
        quotas = [0 for _ in targets]

        if base_count >= len(positive_indices):
            for idx in positive_indices:
                quotas[idx] = 1
            remaining = base_count - len(positive_indices)
            if remaining > 0:
                positive_total = sum(areas[i] for i in positive_indices)
                raw = [
                    ((areas[i] / positive_total) * remaining) if i in positive_indices else 0.0
                    for i in range(len(areas))
                ]
                extra = [int(value) for value in raw]
                for i in range(len(quotas)):
                    quotas[i] += extra[i]

                assigned = sum(quotas)
                if assigned < base_count:
                    remainders = sorted(
                        ((raw[i] - extra[i], i) for i in positive_indices),
                        reverse=True,
                    )
                    for _, idx in remainders[: base_count - assigned]:
                        quotas[idx] += 1
        else:
            top_indices = sorted(positive_indices, key=lambda i: areas[i], reverse=True)[:base_count]
            for idx in top_indices:
                quotas[idx] = 1

    all_transforms = []
    for target_idx, (target, target_quota) in enumerate(zip(targets, quotas)):
        if target_quota <= 0:
            continue
        sample_count = int(round(target_quota * settings.density))
        if settings.mode in {"CHAIN", "GUIDED"}:
            sample_count = max(target_quota, sample_count)
        if sample_count <= 0:
            continue
        samples = sample_target_surface(
            target,
            sample_count,
            settings.distribution,
            settings.random_seed + target_idx * 1000,
            depsgraph=depsgraph,
        )
        transforms = generate_transforms(samples, settings, max_instances=target_quota)
        all_transforms.extend(transforms)

    limit = settings.preview_instances if preview else settings.max_instances
    return all_transforms[:limit]


class BLENDIEARES_OT_use_active_source(bpy.types.Operator):
    bl_idname = "blendie_ares.use_active_source"
    bl_label = "Use Active as Source"
    bl_description = "Assign active object name as source"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.blendie_ares
        active = context.active_object
        if active is None or active.type != "MESH":
            self.report({"ERROR"}, "Active object must be a mesh.")
            return {"CANCELLED"}
        settings.source_object_name = active.name
        return {"FINISHED"}


class BLENDIEARES_OT_use_active_target(bpy.types.Operator):
    bl_idname = "blendie_ares.use_active_target"
    bl_label = "Use Active as Target"
    bl_description = "Assign active object name as target"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.blendie_ares
        active = context.active_object
        if active is None or active.type != "MESH":
            self.report({"ERROR"}, "Active object must be a mesh.")
            return {"CANCELLED"}
        settings.target_object_name = active.name
        return {"FINISHED"}


class BLENDIEARES_OT_preview(bpy.types.Operator):
    bl_idname = "blendie_ares.preview"
    bl_label = "Preview"
    bl_description = "Generate draft preview using linked mesh instances"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.blendie_ares
        source, targets, messages = validate_configuration(context, settings)
        if source is None or not targets:
            for msg in messages:
                self.report({"ERROR"}, msg)
            settings.warning_message = "; ".join(messages)
            return {"CANCELLED"}

        settings.warning_message = "; ".join(messages)
        for msg in messages:
            self.report({"WARNING"}, msg)
        transforms = _compute_transforms_for_targets(context, settings, targets, preview=True)
        if not transforms:
            preview_collection = bpy.data.collections.get(
                _scene_collection_name(settings, PREVIEW_COLLECTION_NAME)
            )
            if preview_collection is not None:
                clear_collection(preview_collection, context.scene, _scene_owner_id(settings))
            self.report(
                {"ERROR"},
                "No instances generated. Check target mesh surface, spacing, density, and mode settings.",
            )
            return {"CANCELLED"}
        _build_instances(
            context,
            source,
            transforms,
            _scene_collection_name(settings, PREVIEW_COLLECTION_NAME),
            _scene_owner_id(settings),
            convert_to_real=False,
            chunk_size=settings.chunk_size,
        )
        self.report({"INFO"}, f"Preview generated: {len(transforms)} instances.")
        return {"FINISHED"}


class BLENDIEARES_OT_apply(bpy.types.Operator):
    bl_idname = "blendie_ares.apply"
    bl_label = "Apply"
    bl_description = "Generate final output using configured settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.blendie_ares
        source, targets, messages = validate_configuration(context, settings)
        if source is None or not targets:
            for msg in messages:
                self.report({"ERROR"}, msg)
            settings.warning_message = "; ".join(messages)
            return {"CANCELLED"}

        settings.warning_message = "; ".join(messages)
        for msg in messages:
            self.report({"WARNING"}, msg)
        transforms = _compute_transforms_for_targets(context, settings, targets, preview=False)
        if not transforms:
            result_collection = bpy.data.collections.get(
                _scene_collection_name(settings, RESULT_COLLECTION_NAME)
            )
            if result_collection is not None:
                clear_collection(result_collection, context.scene, _scene_owner_id(settings))
            self.report(
                {"ERROR"},
                "No instances generated. Check target mesh surface, spacing, density, and mode settings.",
            )
            return {"CANCELLED"}
        _build_instances(
            context,
            source,
            transforms,
            _scene_collection_name(settings, RESULT_COLLECTION_NAME),
            _scene_owner_id(settings),
            convert_to_real=settings.convert_to_real,
            chunk_size=settings.chunk_size,
        )
        preview_collection = bpy.data.collections.get(
            _scene_collection_name(settings, PREVIEW_COLLECTION_NAME)
        )
        if preview_collection is not None:
            clear_collection(preview_collection, context.scene, _scene_owner_id(settings))
        self.report({"INFO"}, f"Applied: {len(transforms)} instances.")
        return {"FINISHED"}


class BLENDIEARES_OT_clear(bpy.types.Operator):
    bl_idname = "blendie_ares.clear_generated"
    bl_label = "Clear Generated"
    bl_description = "Remove generated preview and result objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.blendie_ares
        owner_id = _scene_owner_id(settings)
        remove_collection(
            _scene_collection_name(settings, PREVIEW_COLLECTION_NAME),
            context.scene,
            owner_id=owner_id,
        )
        remove_collection(
            _scene_collection_name(settings, RESULT_COLLECTION_NAME),
            context.scene,
            owner_id=owner_id,
        )
        settings.warning_message = ""
        self.report({"INFO"}, "Cleared generated output.")
        return {"FINISHED"}


CLASSES = (
    BLENDIEARES_OT_use_active_source,
    BLENDIEARES_OT_use_active_target,
    BLENDIEARES_OT_preview,
    BLENDIEARES_OT_apply,
    BLENDIEARES_OT_clear,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
