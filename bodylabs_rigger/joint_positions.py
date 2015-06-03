# Utility function for calculating joint positions relative to a mesh.
#
# Joint specification
# -------------------
# We express the position of a joint by a list of reference vertices and a
# relative position, e.g.
#
#     "Neck": {
#         "reference_vertices": [2319, 482],
#         "relative_position": [0.66, 0.66, 0.66]
#     }
#
# The reference vertices are used to calculate two extrema points. The joint is
# placed along the vector between these extrema points according to the
# relative position.
#
# Extrema point calculation
# -------------------------
# If there are exactly two reference vertices these become the extrema points.
# If there are more than two reference vertices the extrema points are computed
# as the min/max x, y, and z across all vertices.
#
# Relative positioning
# --------------------
# If there is exactly one reference vertex the joint is placed at this vertex.
# Otherwise, the position is calculated relative to the extrema points. A
# relative position vector indicates how much of each dimension to shift from
# the min extrema point to the max extrema point. E.g. if [0.5, 0.5 0.5] is
# used, we'll position the joint half way between the extrema points. If
# [0.25, 0.5, 0.5] is used, we'll position the Joint such that the Y and Z
# positions are half way between the extrema, but the X position is a quarter
# of the way from the min extrema to the max extrema.
#
# Exceptions
# ----------
# 'LeftShoulder' and 'RightShoulder' are positioned 1/3 of the way from the
# 'Neck' to the 'LeftArm' and 'RightArm' joints respectively.


def calculate_joint_position(vertices, reference_vertices,
                             relative_position=[0.5, 0.5, 0.5]):
    import numpy as np

    joint_vertices = vertices[reference_vertices, :].reshape(-1, 3)
    if joint_vertices.shape[0] > 2:
        v1 = np.min(joint_vertices, axis=0)
        v2 = np.max(joint_vertices, axis=0)
    else:
        v1 = joint_vertices[0, :]
        v2 = joint_vertices[-1, :]
    return v1 + (v2 - v1) * np.array(relative_position)


def calculate_joint_positions(vertices, joint_position_spec):
    """Calculate the position of each joint relative to the given vertices.

    vertices: a Vx3 numpy array
    joint_position_spec: a dict mapping joint name to position specification
        (see above for details).

    Returns a map from joint name to target location (as a 3-element numpy
    array) in world coordinates.
    """
    joint_location_map = {}
    for joint_name, joint_spec in joint_position_spec.iteritems():
        joint_location_map[joint_name] = calculate_joint_position(
            vertices, **joint_spec)

    # 'LeftShoulder' and 'RightShoulder' are special cased.
    try:
        neck_pos = joint_location_map['Neck']
        left_arm_pos = joint_location_map['LeftArm']
        joint_location_map['LeftShoulder'] = (
            neck_pos + (left_arm_pos - neck_pos) / 3.
        )
        right_arm_pos = joint_location_map['RightArm']
        joint_location_map['RightShoulder'] = (
            neck_pos + (right_arm_pos - neck_pos) / 3.
        )
    except KeyError as ke:
        print "Unrecognized joint name: '{}'".format(ke)

    return joint_location_map
