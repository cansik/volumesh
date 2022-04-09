from typing import Optional

import numpy as np
import pygltflib

from volumesh.utils import create_data_uri

DRACO_EXTENSION = "KHR_draco_mesh_compression"


class GLTFMeshSequence:
    def __init__(self, scene_name: str = "scene", node_name: str = "sequence",
                 animate: bool = False, frame_rate: int = 24):
        self.sequence_node = pygltflib.Node(name=node_name)
        self.sequence_node.extras.update({
            "frameRate": frame_rate
        })

        self.frame_rate = frame_rate
        self.animate = animate

        self.buffer = pygltflib.Buffer(byteLength=0)
        self.gltf = pygltflib.GLTF2(
            scene=0,
            scenes=[pygltflib.Scene(name=scene_name, nodes=[0])],
            nodes=[self.sequence_node],
            buffers=[self.buffer]
        )

        self.animation = pygltflib.Animation(name="volumesh")
        if self.animate:
            self.gltf.animations.append(self.animation)

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
                    name: str = None,
                    compressed: bool = False,
                    jpeg_textures: bool = False,
                    jpeg_quality: int = 95):
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
        :param jpeg_textures: Use JPEG compression for textures, otherwise PNG
        :return: None
        """

        if name is None:
            name = f"mesh_{len(self.gltf.meshes):05d}"

        # create node
        mesh_index = len(self.gltf.meshes)
        node = pygltflib.Node(mesh=mesh_index, name=name)

        node_index = len(self.gltf.nodes)
        frame_index = len(self.sequence_node.children)
        self.gltf.nodes.append(node)
        self.sequence_node.children.append(node_index)

        # add animation
        if self.animate:
            self._add_frame_rate_animation(node_index, frame_index)

        # create mesh
        accessor_indices_index = len(self.gltf.accessors)
        accessor_position_index = accessor_indices_index + 1

        attributes = pygltflib.Attributes(
            POSITION=accessor_position_index
        )

        primitive = pygltflib.Primitive(attributes=attributes, indices=accessor_indices_index)
        mesh = pygltflib.Mesh(primitives=[primitive])
        self.gltf.meshes.append(mesh)

        # add material
        pbr_material = pygltflib.PbrMetallicRoughness(
            roughnessFactor=0.9,
            metallicFactor=0.1
        )

        material_id = len(self.gltf.materials)
        self.gltf.materials.append(pygltflib.Material(pbrMetallicRoughness=pbr_material))

        # set material
        primitive.material = material_id

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

            if colors is not None and len(colors) > 0:
                attributes.COLOR_0 = len(self.gltf.accessors)
                self._add_vector_data(colors)

            if normals is not None and len(normals) > 0:
                attributes.NORMAL = len(self.gltf.accessors)
                self._add_vector_data(normals)

            if vertex_uvs is not None and len(vertex_uvs) > 0:
                attributes.TEXCOORD_0 = len(self.gltf.accessors)
                self._add_vector_data(vertex_uvs, type=pygltflib.VEC2)

            if texture is not None:
                texture_encoding = "JPEG" if jpeg_textures else "PNG"

                # add image data
                texture_id = len(self.gltf.textures)
                image = pygltflib.Image()
                image.uri = create_data_uri(texture, texture_encoding, jpeg_quality)
                image.name = f"tex_{texture_id:05d}.{texture_encoding.lower()}"
                self.gltf.images.append(image)

                # add sampler
                # todo: maybe only one sampler is needed for volumesh
                self.gltf.samplers.append(pygltflib.Sampler())

                # add texture
                self.gltf.textures.append(pygltflib.Texture(source=texture_id, sampler=texture_id))

            if vertex_uvs is not None and texture is not None:
                # set texture
                pbr_material.baseColorTexture = pygltflib.TextureInfo(index=texture_id)

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
        import DracoPy

        # encode data
        encoded_triangles = np.asarray(triangles).flatten()
        encoded_points = np.asarray(points).flatten()

        result = DracoPy.encode_mesh_to_buffer(encoded_points,
                                               encoded_triangles,
                                               compression_level=10)

        encoded_blob = bytearray(result)

        # ugly hack to get point size back
        # todo: make this more performant
        # version 1.1.0 adds create_metadata attribute
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

    def _add_frame_rate_animation(self, node_index: int, frame_id: int):
        # calculate times
        frame_ms = 1000.0 / self.frame_rate
        frame_start = frame_ms * frame_id / 1000.0
        frame_end = frame_ms * (frame_id + 1) / 1000.0

        # create animation data for times (SCALAR) and scale (VEC3)
        animation_data = np.array([
            [0.0, 0.0, 0.0, 0.0],
            [frame_start, 1.0, 1.0, 1.0],
            [frame_end, 0.0, 0.0, 0.0],
        ], dtype="float32")

        time_key_points = animation_data[:, 0]
        scale_key_points = animation_data[:, 1:]

        times_blob = time_key_points.flatten().tobytes()
        scales_blob = scale_key_points.flatten().tobytes()
        blob = times_blob + scales_blob

        # create time accessor
        times_accessor_index = len(self.gltf.accessors)
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=pygltflib.FLOAT,
                count=time_key_points.shape[0],
                type=pygltflib.SCALAR,
                max=[float(time_key_points.max())],
                min=[float(time_key_points.min())],
            )
        )

        # create scale accessor
        scales_accessor_index = len(self.gltf.accessors)
        self.gltf.accessors.append(
            pygltflib.Accessor(
                bufferView=len(self.gltf.bufferViews),
                componentType=pygltflib.FLOAT,
                count=len(scale_key_points),
                type=pygltflib.VEC3,
                max=scale_key_points.max(axis=0).tolist(),
                min=scale_key_points.min(axis=0).tolist(),
                byteOffset=len(times_blob)
            )
        )

        # add blob
        self.gltf.bufferViews.append(
            pygltflib.BufferView(
                buffer=0,
                byteOffset=len(self.data),
                byteLength=len(blob)
            )
        )

        self.data += blob

        # create animation object
        sampler_index = len(self.animation.samplers)
        self.animation.samplers.append(
            pygltflib.AnimationSampler(
                input=times_accessor_index,
                output=scales_accessor_index,
                interpolation=pygltflib.ANIM_STEP
            )
        )

        self.animation.channels.append(
            pygltflib.AnimationChannel(
                sampler=sampler_index,
                target=pygltflib.AnimationChannelTarget(
                    node=node_index,
                    path="scale"
                )
            )
        )
