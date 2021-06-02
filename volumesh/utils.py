import glob
import os


def get_files_in_path(path: str, extensions: [str] = ["*.*"]):
    return sorted([f for ext in extensions for f in glob.glob(os.path.join(path, ext))])


def get_meshes_in_path(path: str, format: str = "*.obj") -> [str]:
    files = list(sorted(get_files_in_path(path, extensions=[format])))
    return [os.path.abspath(p) for p in files]
