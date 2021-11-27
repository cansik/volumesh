import os

import numpy as np
import pygltflib as pygltflib
from open3d.cpu.pybind.geometry import TriangleMesh
from tqdm import tqdm

from volumesh.GLTFMeshSequence import GLTFMeshSequence


def create_volumesh(meshes: [TriangleMesh],
                    names: [str] = None,
                    compressed: bool = False,
                    jpeg_textures: bool = False) -> pygltflib.GLTF2:
    sequence = GLTFMeshSequence()

    if names is None:
        names = [str(i) for i in range(meshes)]

    with tqdm(desc="volumesh", total=len(meshes)) as prog:
        for i, mesh in enumerate(meshes):
            name = os.path.basename(names[i])

            points = np.float32(np.asarray(mesh.vertices))
            triangles = np.uint32(np.asarray(mesh.triangles))
            colors = np.float32(np.asarray(mesh.vertex_colors))

            # necessary to be GLTF compliant
            mesh = mesh.normalize_normals()
            normals = np.float32(np.asarray(mesh.vertex_normals))

            # convert triangle_uvs into vertex_uvs
            triangle_uvs = np.float32(np.asarray(mesh.triangle_uvs))
            vertex_uvs = _calculate_vertex_uvs(triangles, triangle_uvs)

            textures = [np.asarray(tex) for tex in mesh.textures if not tex.is_empty()]
            texture = textures[0] if len(textures) > 0 else None

            sequence.append_mesh(points, triangles, colors, normals, vertex_uvs, texture,
                                 name=name, compressed=compressed, jpeg_textures=jpeg_textures)
            prog.update()

    gltf = sequence.pack()
    return gltf


def _calculate_vertex_uvs(triangles: np.ndarray, triangle_uvs: np.ndarray) -> np.ndarray:
    # zip triangles & triangle uvs, create a set and sort
    flat_triangle_indices = triangles.flatten()
    flat_triangle_indices = flat_triangle_indices.reshape(*flat_triangle_indices.shape, 1)
    zipped_triangles = np.concatenate((flat_triangle_indices, triangle_uvs), axis=1)
    vertex_uvs = np.float32(np.unique(zipped_triangles, axis=0))
    return vertex_uvs[:, 1:]
