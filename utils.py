import json
import os
import shutil
import zipfile

from PIL import Image
from tqdm import tqdm


def resample_img(img_path: str, save_path: str, limit: int = 2400, quality: int = 100, keep_alpha: bool = False) -> str:
    """
    重采样图片，基于pillow库
    :param img_path: 原始图片路径
    :param save_path: 保存图片路径
    :param limit: 长边限制
    :param quality: 压缩质量
    :param keep_alpha: 是否保留透明度
    :return: 保存图片的文件名
    """
    try:
        img = Image.open(img_path)
        width, height = img.size
        channel = len(img.getbands())
        if width > height and width > limit:
            img = img.resize((limit, int(limit / width * height)))
        elif width <= height and height > limit:
            img = img.resize((int(limit / height * width), limit))
        img = img.convert("RGBA" if (keep_alpha and channel == 4) else "RGB")
        img.save(save_path, **({"quality": quality} if quality != -1 else {}))
        return os.path.split(save_path)[-1]
    except Exception as e:
        return f"[ERR] {e}"


def normalize_path(path: str) -> str:
    """
    去除引号，标准化路径为绝对路径并且确保以斜杠结尾
    :param path: 原始路径
    :return: 标准化后的路径
    """
    path = path.strip("\"").strip("\'")
    path = os.path.abspath(path)
    if os.name == "posix":
        path += "/" if not path.endswith("/") else ""
    else:
        path += "\\" if not path.endswith("\\") else ""
    return path


def recursive_list_file(dir_path: str, res_list=None) -> list:
    """
    递归列出文件夹下所有文件
    :param dir_path: 待列出文件的文件夹路径
    :param res_list: 递归传递的结果列表（不需要传入）
    :return: 文件列表
    """
    if res_list is None:
        res_list = []
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            recursive_list_file(file_path, res_list)
        else:
            res_list.append(file_path)
    return res_list


def filter_images(file_list: list) -> list:
    """
    过滤出图片文件
    :param file_list: 原始文件列表
    :return: 仅包含图片文件的文件列表
    """
    res_list = []
    for filepath in file_list:
        path, file_and_ext = os.path.split(filepath)
        filename, ext = os.path.splitext(file_and_ext)
        if ext.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]:
            res_list.append(filepath)
    return res_list


def load_preset(preset_path: str = "preset.json") -> dict:
    """
    读取预设配置
    :param preset_path: 配置文件路径
    :return: 预设配置
    """
    if not os.path.exists(preset_path):
        return {}
    with open(preset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_relpath_file(dir_path: str) -> list:
    """
    列出文件夹下所有文件的相对路径
    :param dir_path: 待列出文件的文件夹路径
    :return: 文件相对路径列表
    """
    res_list = []
    for foldername, subfolders, filenames in os.walk(dir_path):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)
            res_list.append((file_path, os.path.relpath(file_path, dir_path)))
    return res_list


def make_zipfile(zip_path: str, file_list: list) -> None:
    """
    压缩文件列表
    :param zip_path: 压缩文件路径
    :param file_list: 文件相对路径列表 [(文件路径, 相对路径), ...]
    """
    with zipfile.ZipFile(zip_path, "w") as zipf:
        with tqdm(total=len(file_list), dynamic_ncols=True) as pbar:
            for file_path, rel_path in file_list:
                zipf.write(file_path, rel_path)
                file_name = os.path.split(file_path)[-1]
                pbar.update(1)
                pbar.set_description(f"{file_name}".ljust(24)[:24])


def delete_except_zip(folder_path: str) -> None:
    """
    删除除zip文件外的所有文件
    :param folder_path: 文件夹路径
    """
    for item in os.listdir(folder_path):
        item_path = os.path.join(folder_path, item)

        if item != 'output.zip':
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)
