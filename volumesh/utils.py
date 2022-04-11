import base64
import glob
import os

import cv2
import numpy as np


def get_files_in_path(path: str, extensions: [str] = ["*.*"]):
    return sorted([f for ext in extensions for f in glob.glob(os.path.join(path, ext))])


def get_meshes_in_path(path: str, format: str = "*.obj") -> [str]:
    files = list(sorted(get_files_in_path(path, extensions=[format])))
    return [os.path.abspath(p) for p in files]


def create_data_uri(image: np.ndarray, image_format: str = "PNG", jpeg_quality: int = 75):
    # converts numpy image to data URI
    encode_param = []

    if image_format == "JPEG":
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]

    encode_format = ".jpg" if image_format == "JPEG" else ".png"

    rgb_texture = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    _, encoded_image = cv2.imencode(encode_format, rgb_texture, encode_param)
    data64 = base64.b64encode(encoded_image)
    return u'data:image/' + image_format.lower() + ';base64,' + data64.decode('utf-8')
