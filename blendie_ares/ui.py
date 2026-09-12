import bpy


class BLENDIEARES_PT_main_panel(bpy.types.Panel):
    bl_label = "Blendie Ares"
    bl_idname = "BLENDIEARES_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendie Ares"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.blendie_ares

        source_box = layout.box()
        source_box.label(text="Source Mesh")
        source_box.prop(settings, "source_object_name", text="Object Name")
        source_box.operator("blendie_ares.use_active_source", icon="EYEDROPPER")

        target_box = layout.box()
        target_box.label(text="Target Mesh")
        target_box.prop(settings, "target_object_name", text="Object Name")
        target_box.operator("blendie_ares.use_active_target", icon="EYEDROPPER")
        target_box.prop(settings, "use_selected_targets")

        layout.separator()
        layout.prop(settings, "mode")
        layout.prop(settings, "distribution")
        layout.prop(settings, "density")
        layout.prop(settings, "spacing")
        layout.prop(settings, "contact_tolerance")
        layout.prop(settings, "rotation_jitter_deg")
        layout.prop(settings, "scale_jitter")
        layout.prop(settings, "random_seed")

        perf = layout.box()
        perf.label(text="Performance")
        perf.prop(settings, "preview_instances")
        perf.prop(settings, "max_instances")
        perf.prop(settings, "max_iterations")
        perf.prop(settings, "chunk_size")

        apply_box = layout.box()
        apply_box.prop(settings, "convert_to_real")
        row = apply_box.row(align=True)
        row.operator("blendie_ares.preview", icon="HIDE_OFF")
        row.operator("blendie_ares.apply", icon="CHECKMARK")
        apply_box.operator("blendie_ares.clear_generated", icon="TRASH")

        if settings.warning_message:
            warn = layout.box()
            warn.label(text="Validation", icon="ERROR")
            for line in settings.warning_message.split("; "):
                warn.label(text=line)


CLASSES = (BLENDIEARES_PT_main_panel,)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)

