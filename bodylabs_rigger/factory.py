class RiggedModelFactory(object):
    """Generates rigged models from vertices.

    The factory is initialized with the static data for the model rig: the mesh
    topology and texture map, the joint hierarchy, and the vertex weight map.
    The RiggedModelFactory can then be used to generate FbxScene objects
    binding the rig to a set of mesh vertices.
    """

    def __init__(self, textured_mesh, joint_tree, joint_position_spec,
                 clusters):
        """Initializes the RiggedModelFactory.

        textured_mesh: a TexturedMesh object
        joint_tree: the JointTree at the root of the joint hierarchy
        joint_position_spec: dict mapping joint name to position specification.
            See `joint_positions.py` for more details.
        clusters: dict mapping joint name to ControlPointCluster
        """
        self._textured_mesh = textured_mesh
        self._joint_tree = joint_tree
        self._joint_position_spec = joint_position_spec
        self._clusters = clusters

    def _set_mesh(self, v, fbx_scene):
        """Set the FbxMesh for the given scene.

        v: the mesh vertices
        fbx_scene: the FbxScene to which this mesh should be added

        Returns the FbxNode to which the mesh was added.
        """
        from fbx import (
            FbxLayerElement,
            FbxMesh,
            FbxNode,
            FbxVector2,
            FbxVector4,
        )

        root = fbx_scene.GetRootNode()

        # Create a new node in the scene.
        fbx_mesh_node = FbxNode.Create(fbx_scene, 'BodyLabs_body')
        root.AddChild(fbx_mesh_node)

        fbx_mesh = FbxMesh.Create(fbx_scene, '')
        fbx_mesh_node.SetNodeAttribute(fbx_mesh)

        # Vertices.
        num_vertices = v.shape[0]
        fbx_mesh.InitControlPoints(num_vertices)
        for vi in range(num_vertices):
            new_control_point = FbxVector4(*v[vi, :])
            fbx_mesh.SetControlPointAt(new_control_point, vi)

        # Faces.
        faces = self._textured_mesh.faces
        for fi in range(faces.shape[0]):
            face = faces[fi, :]
            fbx_mesh.BeginPolygon(fi)
            for vi in range(faces.shape[1]):
                fbx_mesh.AddPolygon(face[vi])
            fbx_mesh.EndPolygon()
        fbx_mesh.BuildMeshEdgeArray()

        # Vertex normals.
        fbx_mesh.GenerateNormals(
            False,  # pOverwrite
            True,   # pByCtrlPoint
        )

        # UV map.
        uv_indices = self._textured_mesh.uv_indices.ravel()
        uv_values = self._textured_mesh.uv_values
        uv = fbx_mesh.CreateElementUV('')
        uv.SetMappingMode(FbxLayerElement.eByPolygonVertex)
        uv.SetReferenceMode(FbxLayerElement.eIndexToDirect)
        index_array = uv.GetIndexArray()
        direct_array = uv.GetDirectArray()
        index_array.SetCount(uv_indices.size)
        direct_array.SetCount(uv_values.shape[0])
        for ei, uvi in enumerate(uv_indices):
            index_array.SetAt(ei, uvi)
            direct_array.SetAt(uvi, FbxVector2(*uv_values[uvi, :]))

        return fbx_mesh_node

    def _set_node_translation(self, location, fbx_node):
        """Translates a node to a location in world coordinates.

        location: an unpackable (x, y, z) vector
        fbx_node: the FbxNode to translate
        """
        from fbx import (
            FbxAMatrix,
            FbxDouble4,
            FbxVector4,
        )

        # We want to affect a target global position change by modifying the
        # local node translation. If the global transformation were based
        # solely on translation, rotation, and scale, we could set each of
        # these individually and be done. However, the global transformation
        # matrix computation is more complicated. For details, see
        #   http://help.autodesk.com/view/FBX/2015/ENU/
        #       ?guid=__files_GUID_10CDD63C_79C1_4F2D_BB28_AD2BE65A02ED_htm
        #
        # We get around this by setting the world transform to our desired
        # global translation matrix, then solving for the local translation.
        global_pos_mat = FbxAMatrix()
        global_pos_mat.SetIdentity()
        global_pos_mat.SetT(FbxVector4(*location))

        current_global_pos_mat = fbx_node.EvaluateGlobalTransform()
        parent_global_pos_mat = fbx_node.GetParent().EvaluateGlobalTransform()
        current_local_translation = FbxAMatrix()
        current_local_translation.SetIdentity()
        current_local_translation.SetT(
            FbxVector4(fbx_node.LclTranslation.Get()))
        new_local_translation = (
            parent_global_pos_mat.Inverse() *
            global_pos_mat *
            current_global_pos_mat.Inverse() *
            parent_global_pos_mat *
            current_local_translation
        )
        fbx_node.LclTranslation.Set(FbxDouble4(*new_local_translation.GetT()))

    def _extend_skeleton(self, parent_fbx_node, reference_joint_tree,
                         target_fbx_node_positions, fbx_scene):
        """Extend the FbxNode skeleton according to the reference JointTree.

        parent_fbx_node: the FbxNode off which the skeleton will be extended
        reference_joint_tree: the reference JointTree object providing the
            hierarchy
        target_fbx_node_positions: a mapping from joint name to the desired
           position for the respective FbxNode in the skeleton
        fbx_scene: the FbxScene to which the skeleton should be added

        Returns a map from node name to FbxNode.
        """
        from fbx import (
            FbxNode,
            FbxSkeleton,
        )

        fbx_node_map = {}

        skeleton = FbxSkeleton.Create(fbx_scene, '')
        skeleton.SetSkeletonType(FbxSkeleton.eLimbNode)

        node_name = reference_joint_tree.name
        node = FbxNode.Create(fbx_scene, node_name)
        node.SetNodeAttribute(skeleton)
        parent_fbx_node.AddChild(node)
        fbx_node_map[node_name] = node

        node_position = target_fbx_node_positions.get(node_name, None)
        if node_position is not None:
            self._set_node_translation(node_position, node)
        else:
            print "Position information missing for '{}'".format(node_name)

        for child in reference_joint_tree.children:
            fbx_node_map.update(self._extend_skeleton(
                node, child, target_fbx_node_positions, fbx_scene))
        return fbx_node_map

    def _add_skin_and_bind_pose(self, fbx_node_map, fbx_mesh_node, fbx_scene):
        """Adds a deformer skin and bind pose.

        fbx_node_map: a map from node name to FbxNode. These nodes will become
            the cluster links.
        fbx_mesh_node: the FbxNode where our mesh is attached (i.e. as the
            node attribute). The skin will be added as a deformer of this
            mesh.
        fbx_scene: the FbxScene to which the skin and bind pose should be
            added.
        """
        from fbx import (
            FbxCluster,
            FbxMatrix,
            FbxPose,
            FbxSkin,
        )

        mesh = fbx_mesh_node.GetNodeAttribute()

        skin = FbxSkin.Create(fbx_scene, '')
        bind_pose = FbxPose.Create(fbx_scene, '')
        bind_pose.SetIsBindPose(True)
        bind_pose.Add(fbx_mesh_node, FbxMatrix(
            fbx_mesh_node.EvaluateGlobalTransform()))
        for node_name, node in fbx_node_map.iteritems():
            cluster_info = self._clusters.get(node_name)
            if cluster_info is None:
                continue

            cluster = FbxCluster.Create(fbx_scene, '')
            cluster.SetLink(node)
            cluster.SetLinkMode(FbxCluster.eNormalize)

            vindices = cluster_info.indices
            weights = cluster_info.weights
            for vid, weight in zip(vindices, weights):
                cluster.AddControlPointIndex(vid, weight)

            transform = node.EvaluateGlobalTransform()
            cluster.SetTransformLinkMatrix(transform)
            bind_pose.Add(node, FbxMatrix(transform))
            skin.AddCluster(cluster)
        mesh.AddDeformer(skin)
        fbx_scene.AddPose(bind_pose)

    def construct_rig(self, vertices, fbx_manager):
        from joint_positions import calculate_joint_positions
        from fbx import FbxScene

        fbx_scene = FbxScene.Create(fbx_manager, '')
        fbx_mesh_node = self._set_mesh(vertices, fbx_scene)

        target_joint_positions = calculate_joint_positions(
            vertices, self._joint_position_spec)
        fbx_node_map = self._extend_skeleton(
            fbx_scene.GetRootNode(), self._joint_tree, target_joint_positions,
            fbx_scene)
        self._add_skin_and_bind_pose(fbx_node_map, fbx_mesh_node, fbx_scene)

        return fbx_scene
