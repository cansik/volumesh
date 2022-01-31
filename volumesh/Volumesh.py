import os
from typing import Optional

import cv2
import numpy as np
import pygltflib as pygltflib
from tqdm import tqdm
import open3d as o3d

from volumesh.GLTFMeshSequence import GLTFMeshSequence


class BinaryLengthOverflowException(Exception):
    pass


def create_volumesh(meshes: [o3d.geometry.TriangleMesh],
                    names: [str] = None,
                    compressed: bool = False,
                    jpeg_textures: bool = False,
                    texture_size: Optional[int] = None,
                    animate: bool = False,
                    frame_rate: int = 24
                    ) -> pygltflib.GLTF2:
    sequence = GLTFMeshSequence(animate=animate, frame_rate=frame_rate)

    if names is None:
        names = [str(i) for i in range(meshes)]

    with tqdm(desc="volumesh", total=len(meshes)) as prog:
        for i, mesh in enumerate(meshes):
            name = os.path.basename(names[i])

            # default arguments
            points = np.float32(np.asarray(mesh.vertices))
            triangles = np.uint32(np.asarray(mesh.triangles))

            # optional arguments
            colors = np.float32(np.asarray(mesh.vertex_colors))

            # necessary to be GLTF compliant
            mesh = mesh.normalize_normals()
            normals = np.float32(np.asarray(mesh.vertex_normals))

            # convert triangle_uvs into vertex_uvs
            triangle_uvs = np.float32(np.asarray(mesh.triangle_uvs))
            vertex_uvs = _calculate_vertex_uvs(triangles, triangle_uvs) if len(triangle_uvs) > 0 else None

            textures = [np.asarray(tex) for tex in mesh.textures if not tex.is_empty()]
            texture = textures[0] if len(textures) > 0 else None

            if texture_size is not None:
                h, w = texture.shape[:2]
                texture = cv2.resize(texture, (0, 0), fx=texture_size / w, fy=texture_size / w)

            sequence.append_mesh(points, triangles, colors, normals, vertex_uvs, texture,
                                 name=name, compressed=compressed, jpeg_textures=jpeg_textures)
            prog.update()

    if len(sequence.data) >= pow(2, 32) - 1:
        raise BinaryLengthOverflowException(f"Data size is too large for GLB standard ({len(sequence.data)} bytes).")

    gltf = sequence.pack()
    return gltf


def _calculate_vertex_uvs(triangles: np.ndarray, triangle_uvs: np.ndarray) -> np.ndarray:
    # zip triangles & triangle uvs, create a set and sort
    flat_triangle_indices = triangles.flatten()
    flat_triangle_indices = flat_triangle_indices.reshape(*flat_triangle_indices.shape, 1)
    zipped_triangles = np.concatenate((flat_triangle_indices, triangle_uvs), axis=1)
    vertex_uvs = np.float32(np.unique(zipped_triangles, axis=0))
    return vertex_uvs[:, 1:]
