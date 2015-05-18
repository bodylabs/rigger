# Generates meshes using the the BodyKit API.
#
# For relevant API documentation, see
#     http://developer.bodylabs.com/instant_api_reference.html#Mesh


class MeshGenerator(object):
    _BODYKIT_MESH_ENDPOINT = 'https://api.bodylabs.com/instant/mesh'
    _EXPECTED_VERTICES_PER_MESH = 4916

    def __init__(self, bodykit_access_key, bodykit_secret):
        self._api_access_key = bodykit_access_key
        self._api_secret = bodykit_secret
        self._api_headers = {
            'Authorization': 'SecretPair accesskey={},secret={}'.format(
                bodykit_access_key, bodykit_secret)
        }

    def _request_mesh_obj(self, measurements, unit_system, gender):
        """Requests a mesh from measurements.

        Returns a mesh in OBJ format or None if the request failed.
        """
        import requests

        params = {
            'measurements': measurements,
            'unitSystem': unit_system,
            'gender': gender,
            # Use non-standard measurement set and predict missing
            # measurements.
            'scheme': 'flexible',
            # The rigging code expects a T-posed mesh with quad-based topology.
            'pose': 'T',
            'meshFaces': 'quads',
        }

        response = requests.post(MeshGenerator._BODYKIT_MESH_ENDPOINT,
                                 headers=self._api_headers,
                                 json=params)
        if response.status_code != 200:
            response.raise_for_status()
        return response.text

    def _parse_vertices(self, mesh_obj):
        """Parses the vertices from an OBJ mesh string.

        For background on the OBJ format, see
            http://en.wikipedia.org/wiki/Wavefront_.obj_file

        Returns a Vx3 numpy array, where V is the number of vertices.
        """
        import re
        import numpy as np

        vertex_line_re = re.compile(r'^v (\S+) (\S+) (\S+)$')
        vertices = []
        for line in mesh_obj.split('\n'):
            vertex_match = re.match(vertex_line_re, line)
            if vertex_match is None:
                continue
            try:
                vertices.extend([
                    float(coord) for coord in vertex_match.groups()
                ])
            except ValueError:
                raise ValueError(
                    "Failed to parse float in vertex line: '{}'".format(line))

        # Since we parsed the line, we can assume this is evenly divisible.
        num_vertices = len(vertices) / 3

        # Since the mesh topology doesn't change, we can double check our
        # line parsing by verifying the expected number of vertices.
        if num_vertices != MeshGenerator._EXPECTED_VERTICES_PER_MESH:
            raise ValueError(
                'Mesh has wrong number of vertices: {} vs {}'.format(
                    num_vertices, MeshGenerator._EXPECTED_VERTICES_PER_MESH))

        return np.array(vertices).reshape(-1, 3)

    def get_mesh_for_measurements(self, measurements, unit_system, gender):
        from requests import HTTPError

        try:
            mesh_obj = self._request_mesh_obj(
                measurements, 'unitedStates', gender)
        except HTTPError as e:
            print 'Mesh request failed: {}'.format(e)
            return None

        try:
            return self._parse_vertices(mesh_obj)
        except ValueError as e:
            print 'Failed to parse OBJ vertices: {}'.format(e)
            return None

    def get_random_mesh(self):
        import random

        random.seed(self._api_access_key)

        measurements = {
            'height': random.uniform(60, 80),
            'weight': random.uniform(120, 220),
        }
        gender = random.choice(['male', 'female'])

        return self.get_mesh_for_measurements(
            measurements, 'unitedStates', gender)
