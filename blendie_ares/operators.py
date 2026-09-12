import bpy

from .placement import generate_transforms
from .sampling import sample_target_surface
from .utils import (
    PREVIEW_COLLECTION_NAME,
    RESULT_COLLECTION_NAME,
    clear_collection,
    get_or_create_collection,
    remove_collection,
)
from .validation import validate_configuration


def _build_instances(context, source_obj, transforms, collection_name, convert_to_real, chunk_size):
    clear_collection(collection_name, context.scene)
    collection = get_or_create_collection(context.scene, collection_name)

    created = []
    for idx, matrix in enumerate(transforms, start=1):
        inst = source_obj.copy()
        inst.data = source_obj.data
        inst.animation_data_clear()
        inst.matrix_world = matrix
        collection.objects.link(inst)

        if convert_to_real and inst.type == "MESH" and inst.data is not None:
            inst.data = inst.data.copy()

        created.append(inst)
        if idx % max(1, chunk_size) == 0:
            context.view_layer.update()

    return created


def _compute_transforms_for_targets(context, settings, targets, preview):
    total_target_count = max(1, len(targets))
    base_count = settings.preview_instances if preview else settings.max_instances
    base_per_target = base_count // total_target_count
    remainder = base_count % total_target_count
    depsgraph = context.evaluated_depsgraph_get()

    all_transforms = []
    for target_idx, target in enumerate(targets):
        target_quota = base_per_target + (1 if target_idx < remainder else 0)
        if target_quota <= 0:
            continue
        sample_count = max(1, int(target_quota * settings.density))
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
        _build_instances(
            context,
            source,
            transforms,
            PREVIEW_COLLECTION_NAME,
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
        _build_instances(
            context,
            source,
            transforms,
            RESULT_COLLECTION_NAME,
            convert_to_real=settings.convert_to_real,
            chunk_size=settings.chunk_size,
        )
        clear_collection(PREVIEW_COLLECTION_NAME, context.scene)
        self.report({"INFO"}, f"Applied: {len(transforms)} instances.")
        return {"FINISHED"}


class BLENDIEARES_OT_clear(bpy.types.Operator):
    bl_idname = "blendie_ares.clear_generated"
    bl_label = "Clear Generated"
    bl_description = "Remove generated preview and result objects"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        remove_collection(PREVIEW_COLLECTION_NAME, context.scene)
        remove_collection(RESULT_COLLECTION_NAME, context.scene)
        context.scene.blendie_ares.warning_message = ""
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
