# Volumesh
Utility to create volumetric mesh container files.

## Installation

```
pip install git+https://github.com/cansik/volumesh.git@1.2.2
```

## Usage

To convert a sequence of OBJ files into a volumesh container use the following command:

```bash
volumesh ./human test.glb --compressed
```

First specify the folder where the OBJ's are located (`human`) and then the output file (`test.glb`). Use the compressed flag if you want to compress the container.
The following information will be stored into the mesh if available:

* vertices
* triangle indices
* normals
* vertex-uvs
* textures (png / jpeg)

### Limitations
If draco compression is turned on, only **vertex** and **triangle** information is stored into the mesh. This is due to the fact that [DracoPy](https://github.com/seung-lab/DracoPy) does only support these two primitive values. At the moment we recommend to not use the internal compression, but convert the sequence into a glb file and later convert it using the [gltf-pipeline](https://github.com/CesiumGS/gltf-pipeline). This leads to way better compression and contains still all information parts:

```
gltf-pipeline -i .\sequence.glb -o .\sequence-draco.glb -d
```

### Animation
To use the GLTF animation system to render the meshes in a sequence, it is possible to specify the framerate (default `24`) and set the animation flag.

```
volumesh ./human test.glb --animate --fps 24
```

### Help

```bash
usage: volumesh [-h] [--compressed] [--jpeg-textures] [--animate] [--fps FPS]
                [-tex TEXTURE_SIZE]
                input output

A utility to work with volumesh files.

positional arguments:
  input                 Path to the mesh files (directory).
  output                GLTF output file (file).

optional arguments:
  -h, --help            show this help message and exit
  --compressed          Compress the mesh data.
  --jpeg-textures       Use JPEG compression for textures instead of PNG.
  --animate             Animate mesh frames with GLTF animation system.
  --fps FPS             Animation frames per second (fps).
  -tex TEXTURE_SIZE, --texture-size TEXTURE_SIZE
                        Resize texture to the specified width.
```

## About
Copyright (c) 2022 Zurich University of the Arts ZHdK

![ZHdK Logo](https://lh4.googleusercontent.com/-7NafHJ8zrlE/AAAAAAAAAAI/AAAAAAAAAAA/x4MYabXKMVQ/s88-p-k-no-ns-nd/photo.jpg)