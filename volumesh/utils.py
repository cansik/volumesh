import base64
import glob
import os
from io import BytesIO


def get_files_in_path(path: str, extensions: [str] = ["*.*"]):
    return sorted([f for ext in extensions for f in glob.glob(os.path.join(path, ext))])


def get_meshes_in_path(path: str, format: str = "*.obj") -> [str]:
    files = list(sorted(get_files_in_path(path, extensions=[format])))
    return [os.path.abspath(p) for p in files]


def pil_to_data_uri(img, image_format: str = "PNG"):
    # converts PIL image to datauri
    data = BytesIO()
    img.save(data, image_format)
    data64 = base64.b64encode(data.getvalue())
    return u'data:image/' + image_format.lower() + ';base64,' + data64.decode('utf-8')
