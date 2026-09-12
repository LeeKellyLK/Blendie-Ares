import bpy


class VIEW3D_PT_blendie_ares(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Blendie Ares"
    bl_label = "Blendie Ares"

    def draw(self, context):
        layout = self.layout
        props = context.scene.blendie_ares

        col = layout.column(align=True)
        col.label(text="Objects")
        col.prop(props, "source_object")
        col.prop(props, "target_object")

        col = layout.column(align=True)
        col.label(text="Distribution")
        col.prop(props, "mode")
        col.prop(props, "spacing")
        if props.mode == "SURFACE_FILL":
            col.prop(props, "fill_count")
        col.prop(props, "normal_offset")
        col.prop(props, "seed")

        col = layout.column(align=True)
        col.label(text="Output")
        col.prop(props, "output_collection_name")

        row = layout.row(align=True)
        row.operator("object.blendie_ares_generate", text="Generate")
        row.operator("object.blendie_ares_clear", text="Clear")

        if props.mode == "CHAIN_LINK":
            box = layout.box()
            box.label(text="Chain Link mode:")
            box.label(text="1. Select target mesh")
            box.label(text="2. Enter Edit Mode")
            box.label(text="3. Select one continuous edge loop/path")
