import os
import time

import numpy as np
import open3d as o3d
import pygltflib as pygltflib
from open3d.cpu.pybind.geometry import TriangleMesh
from tqdm import tqdm

from volumesh.GLTFMeshSequence import GLTFMeshSequence


def create_volumesh(meshes: [TriangleMesh], names: [str] = None, compressed: bool = False) -> pygltflib.GLTF2:
    sequence = GLTFMeshSequence()

    if names is None:
        names = [str(i) for i in range(meshes)]

    with tqdm(desc="gltf sequence", total=len(meshes)) as prog:
        for i, mesh in enumerate(meshes):
            name = os.path.basename(names[i])

            points_64 = np.asarray(mesh.vertices, dtype="float64")
            triangles_int32 = np.asarray(mesh.triangles, dtype="int32")

            points = np.float32(points_64)
            triangles = np.uint32(triangles_int32)

            sequence.append_mesh(points, triangles, name=name, compressed=compressed)
            prog.update()

    gltf = sequence.pack()
    return gltf
