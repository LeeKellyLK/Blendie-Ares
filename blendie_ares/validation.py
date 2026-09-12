from mathutils import Vector


def _is_mesh_object(obj):
    return obj is not None and obj.type == "MESH"


def resolve_source(context, settings):
    source = context.scene.objects.get(settings.source_object_name)
    if not _is_mesh_object(source):
        return None, "Source object must be a mesh and exist in scene."
    return source, ""


def resolve_targets(context, settings):
    targets = []
    if settings.use_selected_targets:
        targets = [obj for obj in context.selected_objects if _is_mesh_object(obj)]
    else:
        target = context.scene.objects.get(settings.target_object_name)
        if _is_mesh_object(target):
            targets = [target]

    if not targets:
        return [], "At least one valid mesh target is required."
    return targets, ""


def validate_transforms(source, targets):
    warnings = []

    def has_unapplied_scale(obj):
        scale = obj.scale
        return any(abs(s - 1.0) > 1e-4 for s in scale)

    if has_unapplied_scale(source):
        warnings.append(f"Source '{source.name}' has unapplied scale.")

    mirrored = []
    for t in targets:
        if has_unapplied_scale(t):
            warnings.append(f"Target '{t.name}' has unapplied scale.")
        det = t.matrix_world.to_3x3().determinant()
        if det < 0:
            mirrored.append(t.name)

    if mirrored:
        warnings.append(f"Mirrored target transforms detected: {', '.join(mirrored)}")

    return warnings


def validate_configuration(context, settings):
    source, source_error = resolve_source(context, settings)
    if source_error:
        return None, [], [source_error]

    targets, target_error = resolve_targets(context, settings)
    if target_error:
        return source, [], [target_error]

    warnings = validate_transforms(source, targets)

    if source.name in [t.name for t in targets]:
        warnings.append("Source and target are the same object; result may self-overlap.")

    return source, targets, warnings

