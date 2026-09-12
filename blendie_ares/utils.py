import bpy

PREVIEW_COLLECTION_NAME = "BlendieAres_Preview"
RESULT_COLLECTION_NAME = "BlendieAres_Result"
OWNER_KEY = "blendie_ares_owner"
GENERATED_KEY = "blendie_ares_generated"


def get_or_create_collection(scene: bpy.types.Scene, name: str, owner_id: str) -> bpy.types.Collection:
    collection = bpy.data.collections.get(name)
    if collection is None or collection.get(OWNER_KEY) != owner_id:
        if collection is not None and collection.get(OWNER_KEY) != owner_id:
            name = f"{name}_{owner_id[:6]}"
            collection = bpy.data.collections.get(name)
    if collection is None:
        collection = bpy.data.collections.new(name)
    collection[OWNER_KEY] = owner_id
    if collection.name not in [c.name for c in scene.collection.children]:
        scene.collection.children.link(collection)
    return collection


def clear_collection(collection: bpy.types.Collection, scene: bpy.types.Scene, owner_id: str):
    if collection.get(OWNER_KEY) != owner_id:
        return

    for obj in list(collection.objects):
        if obj.get(GENERATED_KEY):
            bpy.data.objects.remove(obj, do_unlink=True)

    for child in list(collection.children):
        if child.get(OWNER_KEY) == owner_id:
            collection.children.unlink(child)
            _remove_collection_tree(child, scene, owner_id)


def remove_collection(name: str, scene: bpy.types.Scene | None = None, owner_id: str | None = None):
    scene = scene or bpy.context.scene
    collection = bpy.data.collections.get(name)
    if collection is None:
        return

    if owner_id and collection.get(OWNER_KEY) != owner_id:
        return

    _remove_collection_tree(collection, scene, owner_id)


def _remove_collection_tree(
    collection: bpy.types.Collection,
    scene: bpy.types.Scene,
    owner_id: str | None = None,
):
    for child in list(collection.children):
        if owner_id is None or child.get(OWNER_KEY) == owner_id:
            _remove_collection_tree(child, scene, owner_id)

    for obj in list(collection.objects):
        if owner_id is None or obj.get(GENERATED_KEY):
            bpy.data.objects.remove(obj, do_unlink=True)

    for parent in bpy.data.collections:
        if collection.name in [c.name for c in parent.children]:
            parent.children.unlink(collection)

    if collection.name in [c.name for c in scene.collection.children]:
        scene.collection.children.unlink(collection)

    bpy.data.collections.remove(collection)
