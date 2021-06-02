# Volumesh
Tool to create volumetric mesh container files.

## Installation

```
pip install git+https://github.com/cansik/volumesh.git@1.0.0
```

## Usage

To convert a sequence of OBJ files into a volumesh container use the following command:

```bash
volumesh ./human test.glb --compressed
```

First specify the folder where the OBJ's are located (`human`) and then the output file (`test.glb`). Use the compressed flag if you want to compress the container (recommended).

### Help

```bash
usage: volumesh [-h] [--compressed] input output

A utility to work with volumesh files.

positional arguments:
  input         Path to the mesh files (directory).
  output        GLTF output file (file).

optional arguments:
  -h, --help    show this help message and exit
  --compressed  Compress the mesh data.
```

## About
Copyright (c) 2021 Zurich University of the Arts ZHdK
![ZHdK Logo](https://lh4.googleusercontent.com/-7NafHJ8zrlE/AAAAAAAAAAI/AAAAAAAAAAA/x4MYabXKMVQ/s88-p-k-no-ns-nd/photo.jpg)