import bpy

from . import generator


class OBJECT_OT_blendie_ares_generate(bpy.types.Operator):
    bl_idname = "object.blendie_ares_generate"
    bl_label = "Generate Blendie Ares"
    bl_description = "Generate duplicates based on selected mode and settings"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.blendie_ares
        try:
            generator.generate(
                scene=context.scene,
                source_obj=props.source_object,
                target_obj=props.target_object,
                mode=props.mode,
                spacing=props.spacing,
                fill_count=props.fill_count,
                normal_offset=props.normal_offset,
                seed=props.seed,
                output_collection_name=props.output_collection_name,
            )
        except ValueError as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        except Exception as exc:
            self.report({"ERROR"}, f"Unexpected generation error: {exc}")
            return {"CANCELLED"}

        self.report({"INFO"}, "Blendie Ares generation complete")
        return {"FINISHED"}


class OBJECT_OT_blendie_ares_clear(bpy.types.Operator):
    bl_idname = "object.blendie_ares_clear"
    bl_label = "Clear Blendie Ares Output"
    bl_description = "Clear non-destructively generated Blendie Ares duplicates"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.blendie_ares
        try:
            generator.clear(context.scene, props.output_collection_name)
        except Exception as exc:
            self.report({"ERROR"}, f"Unexpected clear error: {exc}")
            return {"CANCELLED"}
        self.report({"INFO"}, "Blendie Ares generated output cleared")
        return {"FINISHED"}
