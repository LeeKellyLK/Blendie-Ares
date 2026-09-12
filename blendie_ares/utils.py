import bpy

PREVIEW_COLLECTION_NAME = "BlendieAres_Preview"
RESULT_COLLECTION_NAME = "BlendieAres_Result"


def get_or_create_collection(scene: bpy.types.Scene, name: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    if collection.name not in [c.name for c in scene.collection.children]:
        scene.collection.children.link(collection)
    return collection


def clear_collection(name: str, scene: bpy.types.Scene | None = None):
    scene = scene or bpy.context.scene
    collection = bpy.data.collections.get(name)
    if collection is None:
        return

    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for child in list(collection.children):
        collection.children.unlink(child)
        _remove_collection_tree(child, scene)


def remove_collection(name: str, scene: bpy.types.Scene | None = None):
    scene = scene or bpy.context.scene
    collection = bpy.data.collections.get(name)
    if collection is None:
        return

    _remove_collection_tree(collection, scene)


def _remove_collection_tree(collection: bpy.types.Collection, scene: bpy.types.Scene):
    for child in list(collection.children):
        _remove_collection_tree(child, scene)

    for obj in list(collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)

    for parent in bpy.data.collections:
        if collection.name in [c.name for c in parent.children]:
            parent.children.unlink(collection)

    if collection.name in [c.name for c in scene.collection.children]:
        scene.collection.children.unlink(collection)

    bpy.data.collections.remove(collection)
