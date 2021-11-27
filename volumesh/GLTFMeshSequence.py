from typing import Optional

import DracoPy
import PIL
import numpy as np
import pygltflib

from volumesh.utils import pil_to_data_uri

DRACO_EXTENSION = "KHR_draco_mesh_compression"


class GLTFMeshSequence:
    def __init__(self, scene_name: str = "scene", node_name: str = "sequence"):
        self.sequence_node = pygltflib.Node(name=node_name)
        self.sequence_node.extras.update({
            "frameRate": 24
        })

        self.buffer = pygltflib.Buffer(byteLength=0)
        self.gltf = pygltflib.GLTF2(
            scene=0,
            scenes=[pygltflib.Scene(name=scene_name, nodes=[0])],
            nodes=[self.sequence_node],
            buffers=[self.buffer]
        )

        self.data: bytearray = bytearray()

    def pack(self) -> pygltflib.GLTF2:
        # update byte length and set data
        self.buffer.byteLength = len(self.data)
        self.gltf.set_binary_blob(self.data)

        return self.gltf

    def append_mesh(self,
                    points: np.array,
                    triangles: np.array,
                    colors: Optional[np.ndarray] = None,
                    normals: Optional[np.ndarray] = None,
                    vertex_uvs: Optional[np.ndarray] = None,
                    texture: Optional[np.ndarray] = None,
                    name: str = None, compressed: bool = False):
        """
        Adds a mesh to the GLTF Sequence.
        :param points: Float32 Numpy Array (n, 3)
        :param triangles: UInt32 Numpy Array (n, 3)
        :param colors: Optional Float32 Numpy Array (n, 3)
        :param normals: Optional Float32 Numpy Array (n, 3)
        :param vertex_uvs: Optional Float32 Numpy Array (n, 3)
        :param texture: Optional UInt32 Numpy Array (u, v, 3)
        :param name: Optional name for the mesh
        :param compressed: Compress the mesh data before adding to the buffer
        :return: None
        """

        if name is None:
            name = f"mesh_{len(self.gltf.meshes):05d}"

        # create node
        mesh_index = len(self.gltf.meshes)
        node = pygltflib.Node(mesh=mesh_index, name=name)

        node_index = len(self.gltf.nodes)
        self.gltf.nodes.append(node)
        self.sequence_node.children.append(node_index)

        # create mesh
        accessor_indices_index = len(self.gltf.accessors)
        accessor_position_index = accessor_indices_index + 1

        attributes = pygltflib.Attributes(
            POSITION=accessor_position_index
        )

        primitive = pygltflib.Primitive(attributes=attributes, indices=accessor_indices_index)
        mesh = pygltflib.Mesh(primitives=[primitive])
        self.gltf.meshes.append(mesh)

        if compressed:
            # compression parts
            if DRACO_EXTENSION not in self.gltf.extensionsUsed:
                self.gltf.extensionsUsed.append(DRACO_EXTENSION)

            if DRACO_EXTENSION not in self.gltf.extensionsRequired:
                self.gltf.extensionsRequired.append(DRACO_EXTENSION)

            # add extension information
            primitive.extensions.update({
                DRACO_EXTENSION: {
                    "bufferView": len(self.gltf.bufferViews),
                    "attributes": {
                        "POSITION": 0,
                    }
                }
            })

            self._add_data_compressed(points, triangles)
        else:
            self._add_triangle_indices(triangles)
            self._add_vector_data(points)

            if colors is not None:
                attributes.COLOR_0 = len(self.gltf.accessors)
                self._add_vector_data(colors)

            if normals is not None:
                # todo: normalize normals first!
                attributes.NORMAL = len(self.gltf.accessors)
                self._add_vector_data(normals)

            if vertex_uvs is not None:
                attributes.TEXCOORD_0 = len(self.gltf.accessors)
                self._add_vector_data(vertex_uvs, type=pygltflib.VEC2)

            if texture is not None:
                # add image data
                # todo: create buffer view for it and append to buffer
                # todo: check power of 2 for texture dimension => already during creation
                image_id = len(self.gltf.textures)
                pil_image = PIL.Image.fromarray(texture).convert('RGB')
                image = pygltflib.Image()
                image.uri = pil_to_data_uri(pil_image, "PNG")
                image.name = f"tex_{image_id:05d}.png"
                self.gltf.images.append(image)

                # add sampler
                # todo: maybe only one sampler is needed for volumesh
                self.gltf.samplers.append(pygltflib.Sampler())

                # add texture
                self.gltf.textures.append(pygltflib.Texture(source=image_id, sampler=image_id))

            if vertex_uvs is not None and texture is not None:
                # add material
                pass

    def _add_triangle_indices(self, triangles: np.array):
        # convert data
        triangles_binary_blob = triangles.flatten().tobytes()

        # triangles
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=pygltflib.UNSIGNED_INT,
                count=triangles.size,
                type=pygltflib.SCALAR,
                max=[int(triangles.max())],
                min=[int(triangles.min())],
            )
        )
        self.gltf.bufferViews.append(
            pygltflib.BufferView(
                buffer=0,
                byteOffset=len(self.data),
                byteLength=len(triangles_binary_blob),
                target=pygltflib.ELEMENT_ARRAY_BUFFER,
            )
        )
        self.data += triangles_binary_blob

    def _add_vector_data(self, array: np.ndarray,
                         component_type: int = pygltflib.FLOAT,
                         type: int = pygltflib.VEC3):
        array_blob = array.tobytes()
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=component_type,
                count=len(array),
                type=type,
                max=array.max(axis=0).tolist(),
                min=array.min(axis=0).tolist(),
            )
        )
        self.gltf.bufferViews.append(
            pygltflib.BufferView(
                buffer=0,
                byteOffset=len(self.data),
                byteLength=len(array_blob),
                target=pygltflib.ARRAY_BUFFER,
            )
        )
        self.data += array_blob

    def _add_data_compressed(self, points: np.array, triangles: np.array):
        # encode data
        encoded_triangles = np.asarray(triangles).flatten()
        encoded_points = np.asarray(points).flatten()

        result = DracoPy.encode_mesh_to_buffer(encoded_points,
                                               encoded_triangles,
                                               compression_level=10)

        encoded_blob = bytearray(result)

        # ugly hack to get point size back
        # todo: make this more performant
        decoded = DracoPy.decode_buffer_to_mesh(encoded_blob)
        triangles_size = len(decoded.faces)
        pts_size = int(len(decoded.points) / 3)

        # 4 bytes padding
        while len(encoded_blob) % 4 != 0:
            encoded_blob.append(0)

        # triangles
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=pygltflib.UNSIGNED_INT,
                count=triangles_size,
                type=pygltflib.SCALAR,
                max=[int(triangles.max())],
                min=[int(triangles.min())],
            )
        )

        # points
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=pygltflib.FLOAT,
                count=pts_size,
                type=pygltflib.VEC3,
                max=points.max(axis=0).tolist(),
                min=points.min(axis=0).tolist(),
            )
        )

        # add blob
        self.gltf.bufferViews.append(
            pygltflib.BufferView(
                buffer=0,
                byteOffset=len(self.data),
                byteLength=len(encoded_blob),
                target=pygltflib.ARRAY_BUFFER,
            )
        )

        self.data += encoded_blob
