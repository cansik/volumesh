import argparse
import os

from volumesh.FastGeometryLoader import load_meshes_fast
from volumesh.Volumesh import create_volumesh
from volumesh.utils import get_meshes_in_path


def parse_arguments():
    a = argparse.ArgumentParser(prog="volumesh",
                                description="A utility to work with volumesh files.")
    a.add_argument("input", help="Path to the mesh files (directory).")
    a.add_argument("output", help="GLTF output file (file).")
    a.add_argument("--compressed", action='store_true', help="Compress the mesh data.")
    args = a.parse_args()
    return args


def main():
    args = parse_arguments()

    # create output folder
    os.makedirs(os.path.dirname(os.path.realpath(args.output)))

    # load meshes
    files = get_meshes_in_path(args.input)
    names = [os.path.splitext(file)[0] for file in files]
    meshes = load_meshes_fast(files)

    # create gltf
    gltf = create_volumesh(meshes, names, compressed=args.compressed)
    gltf.save_binary(args.output)


if __name__ == "__main__":
    main()