import os
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import NumberValidator

from classes import Config, PathValidatorWithoutQuote
from utils import list_all_files, filter_images, load_preset, prepare_resample_tasks, execute_tasks


def print_header(cls: bool = False):
    if cls:
        os.system("clear" if os.name == "posix" else "cls")
    color_print([("green", "图片重采样工具 v3.0"), ("yellow", " @ChrisKimZHT")])


def get_input_output() -> tuple[None, None] | tuple[Path, Path]:
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

    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()

    if input_path == output_path:
        color_print([("red", "[x] 安全起见，输入和输出路径不能相同")])
        return None, None
    if any(output_path.iterdir()):
        color_print([("red", "[x] 安全起见，输出文件夹必须为空")])
        return None, None

    return input_path, output_path


def get_config() -> Config:
    while True:
        input_path, output_path = get_input_output()
        if input_path is not None:
            break

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


def get_image_list(directory: Path) -> list[Path]:
    color_print([("green", "[*] 遍历文件夹中...")])
    img_list = list_all_files(directory)
    color_print([("green", "[*] 遍历完成: "), ("yellow", f"共 {len(img_list)} 个文件")])

    color_print([("green", "[*] 过滤非图片...")])
    img_list = filter_images(img_list)
    color_print([("green", "[*] 过滤完成: "), ("yellow", f"共 {len(img_list)} 个图片")])

    return img_list


def start_process(config: Config, img_list: list[Path]) -> None:
    color_print([("green", "[*] 生成任务...")])
    tasks = prepare_resample_tasks(config, img_list)
    color_print([("green", "[*] 开始任务...")])
    err = execute_tasks(config, tasks)
    color_print([("green", "[*] 处理完成")])

    for i, e in enumerate(err):  # 打印错误信息
        color_print([("red", f"[x] #{i} {e}")])


def main() -> None:
    print_header(cls=True)
    config: Config = get_config()
    img_list = get_image_list(config.input_path)

    if not inquirer.confirm(message="确认开始处理吗?", default=True).execute():
        return

    print_header(cls=True)
    start_process(config, img_list)

    if not inquirer.confirm(message="是否继续?", default=False).execute():
        exit(0)


if __name__ == '__main__':
    while True:
        main()
