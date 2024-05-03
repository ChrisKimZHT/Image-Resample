import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import PathValidator, NumberValidator
from PIL import Image
from tqdm import tqdm


class Config:
    def __init__(self, input_path: str, output_path: str, img_size: int, img_format: str, img_quality: int,
                 concurrency: int):
        self.input_path = input_path
        self.output_path = output_path
        self.img_size = img_size
        self.img_format = img_format
        self.img_quality = img_quality
        self.concurrency = concurrency


def normalize_path(path: str) -> str:
    path = os.path.abspath(path)
    if os.name == "posix":
        path += "/" if not path.endswith("/") else ""
    else:
        path += "\\" if not path.endswith("\\") else ""
    return path


def get_parament() -> Config:
    input_path = inquirer.filepath(
        message="原图文件夹:",
        only_directories=True,
        validate=PathValidator(is_dir=True, is_file=False, message="请输入合法路径"),
    ).execute()
    output_path = inquirer.filepath(
        message="目标文件夹:",
        only_directories=True,
        validate=PathValidator(is_dir=True, is_file=False, message="请输入合法路径"),
    ).execute()
    input_path = normalize_path(input_path)
    output_path = normalize_path(output_path)
    if input_path == output_path:
        color_print([("red", "[x] 安全起见，输入和输出路径不能相同")])
        exit(1)
    if not os.path.exists(input_path):
        color_print([("red", "[x] 输入路径不存在")])
        exit(1)
    if not os.path.exists(output_path):
        color_print([("red", "[x] 安全起见，输出路径必须存在")])
        exit(1)
    img_size = inquirer.text(
        message="尺寸限制 (限制长边，单位像素):",
        validate=NumberValidator(message="请输入合法数字"),
        default="2400",
        filter=lambda result: int(result),
    ).execute()
    img_format = inquirer.select(
        message="压缩格式:",
        choices=["jpg", "webp"],
    ).execute()
    img_quality = inquirer.text(
        message="压缩质量 (1-100):",
        validate=NumberValidator(message="请输入合法数字"),
        default="90",
        filter=lambda result: int(result),
    ).execute()
    concurrency = inquirer.text(
        message="并行数:",
        validate=NumberValidator(message="请输入合法数字"),
        default="8",
        filter=lambda result: int(result),
    ).execute()
    config = Config(input_path, output_path, img_size, img_format, img_quality, concurrency)
    return config


def get_filepath(dir_path: str, res_list: list) -> list:
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            get_filepath(file_path, res_list)
        else:
            res_list.append(file_path)
    return res_list


def filter_filepath(file_list: list) -> list:
    res_list = []
    for filepath in file_list:
        path, file_and_ext = os.path.split(filepath)
        filename, ext = os.path.splitext(file_and_ext)
        if ext.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]:
            res_list.append(filepath)
    return res_list


def resample_img(img_path: str, save_path: str, limit: int = 2400, quality: int = 100) -> str:
    img = Image.open(img_path)
    width, height = img.size
    if width > height and width > limit:
        img = img.resize((limit, int(limit / width * height)))
    elif width <= height and height > limit:
        img = img.resize((int(limit / height * width), limit))
    img.convert("RGB").save(save_path, quality=quality)
    return os.path.split(save_path)[-1]


def prepare_tasks(config: Config, img_list: list) -> list:
    tasks = []
    with tqdm(total=len(img_list), dynamic_ncols=True) as pbar:
        for img_path in img_list:
            path, file_and_ext = os.path.split(img_path)
            file, ext = os.path.splitext(file_and_ext)
            new_path = path.replace(config.input_path, config.output_path)
            save_path = os.path.join(new_path, f"{file}.{config.img_format}")
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            tasks.append((resample_img, img_path, save_path, config.img_size, config.img_quality))
            pbar.set_description(f"{file_and_ext}".ljust(24)[:24])
            pbar.update(1)
    return tasks


def execute_tasks(config: Config, tasks: list) -> None:
    with ThreadPoolExecutor(max_workers=config.concurrency) as executor:
        futures = [executor.submit(*task) for task in tasks]
        with tqdm(total=len(futures), dynamic_ncols=True) as pbar:
            for future in as_completed(futures):
                pbar.set_description(f"{future.result()}".ljust(24)[:24])
                pbar.update(1)


def main() -> None:
    color_print([("green", "图片重采样工具 v2.1"), ("yellow", " @ChrisKimZHT")])
    config: Config = get_parament()
    color_print([("green", "[*] 遍历文件夹中...")])
    img_list = get_filepath(config.input_path, [])
    color_print([("green", "[*] 遍历完成: "), ("yellow", f"共 {len(img_list)} 个文件")])
    color_print([("green", "[*] 过滤非图片...")])
    img_list = filter_filepath(img_list)
    color_print([("green", "[*] 过滤完成: "), ("yellow", f"共 {len(img_list)} 个图片")])
    confirm = inquirer.confirm(
        message="确认开始处理吗?",
        default=True,
    ).execute()
    if not confirm:
        exit()
    os.system("clear" if os.name == "posix" else "cls")
    color_print([("green", "图片重采样工具 v2.1"), ("yellow", " @ChrisKimZHT")])
    color_print([("green", "[*] 生成任务...")])
    tasks = prepare_tasks(config, img_list)
    color_print([("green", "[*] 开始任务...")])
    execute_tasks(config, tasks)
    color_print([("green", "[*] 处理完成")])
    is_continue = inquirer.confirm(
        message="是否继续?",
        default=False,
    ).execute()
    if not is_continue:
        exit(0)


if __name__ == '__main__':
    while True:
        main()
