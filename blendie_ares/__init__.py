bl_info = {
    "name": "Blendie Ares",
    "author": "Blendie-Ares Contributors",
    "version": (0, 1, 0),
    "blender": (5, 2, 1),
    "location": "View3D > Sidebar > Blendie Ares",
    "description": "Distribute a source mesh over a target mesh using fill and edge-loop chain modes",
    "category": "Object",
}

import bpy

from .properties import BlendieAresProperties
from .operators import OBJECT_OT_blendie_ares_generate, OBJECT_OT_blendie_ares_clear
from .panel import VIEW3D_PT_blendie_ares

CLASSES = (
    BlendieAresProperties,
    OBJECT_OT_blendie_ares_generate,
    OBJECT_OT_blendie_ares_clear,
    VIEW3D_PT_blendie_ares,
)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.blendie_ares = bpy.props.PointerProperty(type=BlendieAresProperties)


def unregister():
    del bpy.types.Scene.blendie_ares
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
