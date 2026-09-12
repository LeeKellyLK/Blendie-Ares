import bpy


class BlendieAresProperties(bpy.types.PropertyGroup):
    source_object: bpy.props.PointerProperty(
        name="Source Tile",
        description="Single mesh object to duplicate",
        type=bpy.types.Object,
    )
    target_object: bpy.props.PointerProperty(
        name="Target Mesh",
        description="Mesh object to populate",
        type=bpy.types.Object,
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=(
            ("SURFACE_FILL", "Surface Fill", "Fill target surface with spaced duplicates"),
            ("CHAIN_LINK", "Chain Link", "Follow selected target edge loop"),
        ),
        default="SURFACE_FILL",
    )
    spacing: bpy.props.FloatProperty(
        name="Spacing",
        description="Minimum spacing between generated items",
        min=0.0001,
        default=0.25,
    )
    fill_count: bpy.props.IntProperty(
        name="Fill Count",
        description="Maximum duplicate count for surface fill mode",
        min=1,
        default=150,
    )
    normal_offset: bpy.props.FloatProperty(
        name="Normal Offset",
        description="Offset along surface normal to avoid overlap/z-fighting",
        default=0.0,
    )
    seed: bpy.props.IntProperty(
        name="Seed",
        description="Random seed for repeatable generation",
        default=0,
    )
    output_collection_name: bpy.props.StringProperty(
        name="Output Collection",
        description="Collection used for non-destructive generated output",
        default="BlendieAres_Generated",
    )
