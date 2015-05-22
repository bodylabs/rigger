# Utilities functions for working with an FbxScene.
#
# Example usage:
#
#     manager = create_fbx_manager()
#     scene = import_fbx_scene(manager, 'path/to/scene.fbx')
#
#     # ... Make some changes ...
#
#     export_fbx_scene(manager, scene, 'path/to/scene_modified.fbx')
#     manager.Destroy()
#     # Delete the (now unusable) FbxManager to avoid accidental
#     # usage in later code.
#     del manager


def create_fbx_manager():
    from fbx import (
        FbxIOSettings,
        FbxManager,
        IOSROOT,
    )

    fbx_manager = FbxManager.Create()
    if not fbx_manager:
        raise RuntimeError('Failed to create FbxManager.')
    ios = FbxIOSettings.Create(fbx_manager, IOSROOT)
    fbx_manager.SetIOSettings(ios)
    return fbx_manager


def import_fbx_scene(fbx_manager, scene_path):
    from fbx import (
        FbxImporter,
        FbxScene,
    )

    importer = FbxImporter.Create(fbx_manager, '')
    # Import with any file format.
    if not importer.Initialize(scene_path, -1, fbx_manager.GetIOSettings()):
        raise IOError('Failed to import scene file: {}'.format(scene_path))

    scene = FbxScene.Create(fbx_manager, '')
    importer.Import(scene)
    importer.Destroy()
    return scene


def export_fbx_scene(fbx_manager, scene, output_path):
    import os
    from fbx import FbxExporter

    output_path = os.path.expanduser(output_path)

    exporter = FbxExporter.Create(fbx_manager, '')
    exporter.Initialize(output_path, -1, fbx_manager.GetIOSettings())
    exporter.Export(scene)
    exporter.Destroy()
    return output_path
