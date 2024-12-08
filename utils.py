import json
import os
from pathlib import Path

from PIL import Image


def resample_img(img_path: Path, save_path: Path, limit: int = 2400, quality: int = 100,
                 keep_alpha: bool = False) -> str:
    """
    重采样图片，基于pillow库
    :param img_path: 原始图片路径
    :param save_path: 保存图片路径
    :param limit: 长边限制
    :param quality: 压缩质量
    :param keep_alpha: 是否保留透明度
    :return: 保存图片的文件名，如果以[ERR]开头则表示出错
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
        return save_path.name
    except Exception as e:
        return f"[ERR] {e}"


def list_all_files(directory: Path) -> list[Path]:
    """
    列出文件夹下所有文件
    :param directory: 文件夹路径
    :return: 文件列表
    """
    return [file for file in Path(directory).rglob('*') if file.is_file()]


def filter_images(file_list: list[Path]) -> list[Path]:
    """
    过滤出图片文件
    :param file_list: 原始文件列表
    :return: 仅包含图片文件的文件列表
    """
    image_extensions = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]
    return [filepath for filepath in file_list if (filepath.suffix.lower() in image_extensions)]


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


if __name__ == "__main__":
    print(list_all_files(Path("D:\\Downloads")))
