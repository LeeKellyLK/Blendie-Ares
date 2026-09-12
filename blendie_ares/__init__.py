bl_info = {
    "name": "Blendie Ares",
    "author": "LeeKellyLK",
    "version": (0, 1, 0),
    "blender": (5, 2, 1),
    "location": "View3D > Sidebar > Blendie Ares",
    "description": "Distribute a source mesh across target surfaces in chain/fill/guided modes",
    "category": "Object",
}

if all(name in locals() for name in ("operators", "properties", "ui")):
    import importlib

    importlib.reload(properties)
    importlib.reload(operators)
    importlib.reload(ui)
else:
    from . import operators, properties, ui


def register():
    properties.register()
    operators.register()
    ui.register()


def unregister():
    ui.unregister()
    operators.unregister()
    properties.unregister()

