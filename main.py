import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import NumberValidator
from tqdm import tqdm

from classes import Config, PathValidatorWithoutQuote
from utils import normalize_path, recursive_list_file, filter_images, resample_img, load_preset


def get_parament() -> Config:
    input_path = inquirer.filepath(
        message="原图文件夹:",
        only_directories=True,
        validate=PathValidatorWithoutQuote(is_dir=True, is_file=False, message="请输入合法路径"),
    ).execute()
    output_path = inquirer.filepath(
        message="目标文件夹:",
        only_directories=True,
        validate=PathValidatorWithoutQuote(is_dir=True, is_file=False, message="请输入合法路径"),
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

    preset = load_preset()
    config = Config(input_path=input_path, output_path=output_path)

    if preset != {}:
        color_print([("green", "[*] 检测到预设配置如下:")])
        for k, v in preset.items():
            color_print([("green", f"  - {k}: {v}")])
        confirm = inquirer.confirm(
            message="是否使用?",
            default=True,
        ).execute()
        if not confirm:
            preset = {}

    config.img_size = inquirer.text(
        message="尺寸限制 (限制长边，单位像素):",
        validate=NumberValidator(message="请输入合法数字"),
        default="2400",
        filter=lambda result: int(result),
    ).execute() if ("img_size" not in preset) else preset["img_size"]

    config.img_format = inquirer.select(
        message="压缩格式:",
        choices=["jpg", "webp", "png"],
    ).execute() if ("img_format" not in preset) else preset["img_format"]

    if config.img_format != "png":
        config.img_quality = inquirer.text(
            message="压缩质量 (1-100):",
            validate=NumberValidator(message="请输入合法数字"),
            default="90",
            filter=lambda result: int(result),
        ).execute() if ("img_quality" not in preset) else preset["img_quality"]

    if config.img_format != "jpg":
        config.keep_alpha = inquirer.confirm(
            message="是否保留透明度?",
            default=True,
        ).execute() if ("keep_alpha" not in preset) else preset["keep_alpha"]

    config.concurrency = inquirer.text(
        message="并行数:",
        validate=NumberValidator(message="请输入合法数字"),
        default="8",
        filter=lambda result: int(result),
    ).execute() if ("concurrency" not in preset) else preset["concurrency"]

    return config


def prepare_tasks(config: Config, img_list: list) -> list:
    tasks = []
    with tqdm(total=len(img_list), dynamic_ncols=True) as pbar:
        for img_path in img_list:
            path, file_and_ext = os.path.split(img_path)
            file, ext = os.path.splitext(file_and_ext)
            new_path = normalize_path(path).replace(config.input_path, config.output_path)
            save_path = os.path.join(new_path, f"{file}.{config.img_format}")
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            tasks.append((resample_img, img_path, save_path, config.img_size, config.img_quality, config.keep_alpha))
            pbar.set_description(f"{file_and_ext}".ljust(24)[:24])
            pbar.update(1)
    return tasks


def execute_tasks(config: Config, tasks: list) -> list:
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


def main() -> None:
    color_print([("green", "图片重采样工具 v2.2"), ("yellow", " @ChrisKimZHT")])
    config: Config = get_parament()
    color_print([("green", "[*] 遍历文件夹中...")])
    img_list = recursive_list_file(config.input_path)
    color_print([("green", "[*] 遍历完成: "), ("yellow", f"共 {len(img_list)} 个文件")])
    color_print([("green", "[*] 过滤非图片...")])
    img_list = filter_images(img_list)
    color_print([("green", "[*] 过滤完成: "), ("yellow", f"共 {len(img_list)} 个图片")])
    confirm = inquirer.confirm(
        message="确认开始处理吗?",
        default=True,
    ).execute()
    if not confirm:
        exit()
    os.system("clear" if os.name == "posix" else "cls")
    color_print([("green", "图片重采样工具 v2.2"), ("yellow", " @ChrisKimZHT")])
    color_print([("green", "[*] 生成任务...")])
    tasks = prepare_tasks(config, img_list)
    color_print([("green", "[*] 开始任务...")])
    err = execute_tasks(config, tasks)
    color_print([("green", "[*] 处理完成")])
    for i, e in enumerate(err):
        color_print([("red", f"[x] #{i} {e}")])
    is_continue = inquirer.confirm(
        message="是否继续?",
        default=False,
    ).execute()
    if not is_continue:
        exit(0)


if __name__ == '__main__':
    while True:
        main()
