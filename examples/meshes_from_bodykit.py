# Randomly generates and rigs a set of meshes.
#
# Requires access to BodyKit, which can be requested at http://bodykit.io/.


def main():
    import os
    import argparse
    import bodylabs_rigger.static
    from bodylabs_rigger.factory import RiggedModelFactory
    from bodylabs_rigger.fbx_util import (
        create_fbx_manager,
        export_fbx_scene,
    )
    from bodylabs_rigger.rig_assets import RigAssets
    from mesh_generator import MeshGenerator

    access_key = os.environ.get('BODYKIT_ACCESS_KEY', None)
    secret = os.environ.get('BODYKIT_SECRET', None)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'output_directory', default=None,
        help='The directory to write the rigged meshes.')

    parser.add_argument(
        '--num_meshes', default=5, type=int, required=False,
        help='The number of meshes to generate and rig.')
    parser.add_argument(
        '--bodykit_access_key', default=None, required=(access_key is None),
        help=('Access key for the BodyKit API. Required if BODYKIT_ACCESS_KEY '
              'environment variable is not set.'))
    parser.add_argument(
        '--bodykit_secret', default=None, required=(secret is None),
        help=('Secret for the BodyKit API. Required if BODYKIT_SECRET '
              'environment variable is not set.'))
    args = parser.parse_args()

    access_key = args.bodykit_access_key or access_key
    secret = args.bodykit_secret or secret

    mesh_generator = MeshGenerator(access_key, secret)

    # Load rigging assets and initialize the rigging factory.
    assets = RigAssets.load(os.path.join(
        os.path.dirname(bodylabs_rigger.static.__file__),
        'rig_assets.json'))
    factory = RiggedModelFactory(**assets.__dict__)

    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    manager = create_fbx_manager()
    for mesh_index in range(args.num_meshes):
        print 'Generating rigged mesh {}'.format(mesh_index)
        mesh = mesh_generator.get_random_mesh()
        if mesh is None:
            continue

        rigged_mesh = factory.construct_rig(mesh, manager)
        output_path = os.path.join(
            args.output_directory, 'rigged_mesh_{:02}.fbx'.format(mesh_index))
        export_fbx_scene(manager, rigged_mesh, output_path)
        rigged_mesh.Destroy()
    manager.Destroy()


if __name__ == '__main__':
    main()
