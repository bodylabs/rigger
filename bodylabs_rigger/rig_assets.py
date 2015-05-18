class RigAssets(object):
    """Serializable wrapper for dependencies of a RiggedModelFactory."""

    def __init__(self, textured_mesh, joint_tree, joint_position_spec,
                 clusters):
        self.textured_mesh = textured_mesh
        self.joint_tree = joint_tree
        self.joint_position_spec = joint_position_spec
        self.clusters = clusters

    def to_json(self):
        return {
            'textured_mesh': self.textured_mesh.to_json(),
            'joint_tree': self.joint_tree.to_json(),
            # The joint position spec is already JSON serializable.
            'joint_position_spec': self.joint_position_spec,
            'clusters': {
                name: cluster.to_json()
                for name, cluster in self.clusters.iteritems()
            }
        }

    @classmethod
    def from_json(cls, o):
        return cls(
            textured_mesh=TexturedMesh.from_json(o['textured_mesh']),
            joint_tree=JointTree.from_json(o['joint_tree']),
            joint_position_spec=o['joint_position_spec'],
            clusters={
                name: ControlPointCluster.from_json(cluster)
                for name, cluster in o['clusters'].iteritems()
            }
        )

    def dump(self, filename):
        import json

        with open(filename, 'w') as f:
            json.dump(self.to_json(), f)

    @classmethod
    def load(cls, filename):
        import json

        with open(filename, 'r') as f:
            assets = cls.from_json(json.load(f))
        return assets


class JointTree(object):
    """A simple tree-based representation for a hierarchy of joints."""

    def __init__(self, name, children=None):
        """Initialize the joint subtree.

        name: the name for this joint
        children: a list of JointTree objects
        """
        self.name = name
        self.children = children
        if self.children is None:
            self.children = []

    def to_json(self):
        return {
            'name': self.name,
            'children': [c.to_json() for c in self.children]
        }

    @classmethod
    def from_json(cls, o):
        return cls(o['name'], [cls.from_json(c) for c in o['children']])


class TexturedMesh(object):
    """Wrapper for the faces and corresponding texture map of a mesh."""

    def __init__(self, faces, uv_indices, uv_values):
        """Initializes the TexturedMesh.

        Let F denote the number of faces in the mesh.

        faces: Fx4 numpy array of vertex indices (four per face).
        uv_indices: Fx4 numpy array of `uv_values` row indices.
        uv_values: each row gives the U and V coordinates for a particular
            face vertex.
        """
        self.faces = faces
        self.uv_indices = uv_indices
        self.uv_values = uv_values

    def to_json(self):
        # Flatten each numpy array.
        return {k: v.ravel().tolist() for k, v in self.__dict__.iteritems()}

    @classmethod
    def from_json(cls, o):
        import numpy as np
        return cls(
            faces=np.array(o['faces']).reshape(-1, 4),
            uv_indices=np.array(o['uv_indices']).reshape(-1, 4),
            uv_values=np.array(o['uv_values']).reshape(-1, 2),
        )


class ControlPointCluster(object):
    """Wrapper for the indices and weights of a vertex control cluster."""

    def __init__(self, indices, weights):
        self.indices = indices
        self.weights = weights

    def to_json(self):
        return self.__dict__

    @classmethod
    def from_json(cls, o):
        return cls(**o)
