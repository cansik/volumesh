import argparse
import os
import open3d as o3d

from tqdm import tqdm

from volumesh.FastGeometryLoader import load_meshes_fast, load_meshes_safe
from volumesh.Volumesh import create_volumesh
from volumesh.utils import get_meshes_in_path


def parse_arguments():
    a = argparse.ArgumentParser(prog="volumesh",
                                description="A utility to work with volumesh files.")
    a.add_argument("input", help="Path to the mesh files (directory).")
    a.add_argument("output", help="GLTF output file (file).")
    a.add_argument("--compressed", action='store_true', help="Compress the mesh data.")
    a.add_argument("--jpeg-textures", action='store_true', help="Use JPEG compression for textures instead of PNG.")
    a.add_argument("--animate", action='store_true', help="Animate mesh frames with GLTF animation system.")
    a.add_argument("--fps", type=int, default=24, help="Animation frames per second (fps).")
    a.add_argument("-tex", "--texture-size", type=int, default=None, help="Resize texture to the specified width.")
    a.add_argument("--load-safe", action='store_true', help="Load meshes slow but save.")
    a.add_argument("--simplify", action='store_true', help="Simplify the mesh to reduce file size.")
    args = a.parse_args()
    args.output = os.path.abspath(args.output)
    return args


def pre_process_mesh(mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
    mesh = mesh.simplify_vertex_clustering(
        voxel_size=9.731187e-03,
        contraction=o3d.geometry.SimplificationContraction.Average)
    return mesh


def main():
    args = parse_arguments()

    # create output folder
    output_dir = os.path.dirname(os.path.realpath(args.output))
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # load meshes
    files = get_meshes_in_path(args.input)
    names = [os.path.splitext(file)[0] for file in files]

    process_method = None
    if args.simplify:
        process_method = pre_process_mesh

    if args.load_safe:
        meshes = load_meshes_safe(files, post_processing=True, process_mesh=process_method)
    else:
        meshes = load_meshes_fast(files, post_processing=True, process_mesh=process_method)

    # create gltf
    gltf = create_volumesh(meshes, names, compressed=args.compressed,
                           jpeg_textures=args.jpeg_textures, texture_size=args.texture_size,
                           animate=args.animate, frame_rate=args.fps)

    # save to disk
    with tqdm(desc="saving", total=1) as prog:
        gltf.save_binary(args.output)
        prog.update()


if __name__ == "__main__":
    main()
