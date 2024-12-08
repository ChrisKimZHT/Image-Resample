import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from PIL import Image
from tqdm import tqdm

from classes import Config


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


def prepare_resample_tasks(config: Config, img_list: list[Path]) -> list[tuple]:
    """
    生成重采样任务列表
    :param config: 任务配置
    :param img_list: 图片列表
    :return: 任务列表
    """
    tasks = []
    with tqdm(total=len(img_list), dynamic_ncols=True) as pbar:
        for img_path in img_list:
            old_path = img_path.parent
            new_path = config.output_path / old_path.relative_to(config.input_path)  # 保留原文件夹结构
            if not new_path.exists():
                new_path.mkdir(parents=True)

            file_name, file_ext = img_path.name, img_path.suffix
            save_img_path = new_path / file_name

            tasks.append((resample_img, img_path, save_img_path,
                          config.img_size, config.img_quality, config.keep_alpha))
            pbar.set_description(f"{file_name}.{file_ext}".ljust(24)[:24])
            pbar.update(1)
    return tasks


def execute_tasks(config: Config, tasks: list) -> list:
    """
    执行任务列表
    :param config: 任务配置
    :param tasks: 任务列表
    :return: 错误列表
    """
    err = []
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [executor.submit(*task) for task in tasks]
        with tqdm(total=len(futures), dynamic_ncols=True) as pbar:
            for future in as_completed(futures):
                res = future.result()
                if res.startswith("[ERR] "):
                    err.append(res[6:])
                pbar.set_description(f"{res}".ljust(24)[:24])
                pbar.update(1)
    return err


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
