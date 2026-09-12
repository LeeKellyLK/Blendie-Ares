import bpy


class BlendieAresProperties(bpy.types.PropertyGroup):
    scene_uid: bpy.props.StringProperty(default="", options={"HIDDEN"})
    source_object_name: bpy.props.StringProperty(name="Source")
    target_object_name: bpy.props.StringProperty(name="Target")
    use_selected_targets: bpy.props.BoolProperty(
        name="Use Selected Targets",
        description="Use all selected mesh objects as targets",
        default=False,
    )
    mode: bpy.props.EnumProperty(
        name="Mode",
        items=[
            ("CHAIN", "Chain", "Linked/adjacent chain-like placement"),
            ("FILL", "Fill", "Surface coverage with contact tolerance"),
            ("GUIDED", "Guided", "Follow sampled tangent flow"),
        ],
        default="CHAIN",
    )
    distribution: bpy.props.EnumProperty(
        name="Distribution",
        items=[
            ("UNIFORM", "Uniform", "Cycle triangles in order"),
            ("RANDOM", "Random", "Random triangles with equal chance"),
            ("WEIGHTED", "Weighted", "Sample triangles by area"),
        ],
        default="WEIGHTED",
    )
    density: bpy.props.FloatProperty(
        name="Density",
        default=1.0,
        min=0.1,
        max=5.0,
        description="Density multiplier for generated points",
    )
    spacing: bpy.props.FloatProperty(
        name="Spacing",
        default=0.1,
        min=0.001,
        soft_max=10.0,
    )
    contact_tolerance: bpy.props.FloatProperty(
        name="Contact Tolerance",
        default=0.15,
        min=0.0,
        max=1.0,
        description="Tolerance used for near-touching placement",
    )
    rotation_jitter_deg: bpy.props.FloatProperty(
        name="Rotation Jitter (°)",
        default=5.0,
        min=0.0,
        max=180.0,
    )
    scale_jitter: bpy.props.FloatProperty(
        name="Scale Jitter",
        default=0.0,
        min=0.0,
        max=1.0,
        description="Random uniform scale variation (+/-)",
    )
    random_seed: bpy.props.IntProperty(name="Seed", default=0, min=0)
    max_instances: bpy.props.IntProperty(
        name="Max Instances",
        default=400,
        min=1,
        max=50000,
    )
    preview_instances: bpy.props.IntProperty(
        name="Preview Count",
        default=120,
        min=1,
        max=20000,
    )
    max_iterations: bpy.props.IntProperty(
        name="Max Iterations",
        default=4000,
        min=1,
        max=200000,
        description="Bounded iteration budget for placement loops",
    )
    chunk_size: bpy.props.IntProperty(
        name="Chunk Size",
        default=200,
        min=10,
        max=5000,
        description="Processing batch size for larger outputs",
    )
    convert_to_real: bpy.props.BoolProperty(
        name="Convert to Real",
        default=False,
        description="Make generated objects unique meshes on apply",
    )
    warning_message: bpy.props.StringProperty(default="")


def register():
    bpy.utils.register_class(BlendieAresProperties)
    bpy.types.Scene.blendie_ares = bpy.props.PointerProperty(type=BlendieAresProperties)


def unregister():
    del bpy.types.Scene.blendie_ares
    bpy.utils.unregister_class(BlendieAresProperties)
