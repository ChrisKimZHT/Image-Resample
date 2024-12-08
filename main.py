import os
import shutil
import tempfile
from pathlib import Path

from InquirerPy import inquirer
from InquirerPy.utils import color_print
from InquirerPy.validator import NumberValidator

from classes import Config, PathValidatorWithoutQuote
from utils import list_all_files, filter_images, load_preset, prepare_resample_tasks, execute_tasks, parse_concurrency, \
    unzip_to_tmp, make_zip


def print_header(cls: bool = False) -> None:
    if cls:
        os.system("clear" if os.name == "posix" else "cls")
    color_print([("green", "图片重采样工具 v3.0"), ("yellow", " @ChrisKimZHT")])


def get_input_output() -> tuple[None, None] | tuple[Path, Path]:
    input_path = inquirer.filepath(
        message="原图文件夹或压缩包:",
        validate=PathValidatorWithoutQuote(message="请输入合法路径"),
    ).execute()
    output_path = inquirer.filepath(
        message="目标文件夹或压缩包:",
    ).execute()

    input_path = Path(input_path).resolve()
    output_path = Path(output_path).resolve()

    if input_path == output_path:
        color_print([("red", "[x] 安全起见，输入和输出路径不能相同")])
        return None, None

    if not input_path.exists():
        color_print([("red", "[x] 输入路径不存在")])
        return None, None
    # 此时 input_path 一定存在

    if input_path.is_file() and input_path.suffix.lower() != ".zip":
        color_print([("red", "[x] 压缩包必须是 zip 格式")])
        return None, None
    # 此时 input_path 一定是文件夹或 zip 压缩包

    if output_path.exists():
        if output_path.is_file():
            color_print([("red", "[x] 安全起见，不可覆盖已存在文件")])
            return None, None
        if output_path.is_dir() and any(output_path.iterdir()):
            color_print([("red", "[x] 安全起见，输出文件夹必须为空")])
            return None, None
    else:  # output_path 不存在
        if output_path.suffix.lower() == ".zip":
            output_path.touch()
            assert output_path.is_file()
        else:
            output_path.mkdir(parents=True)
            assert output_path.is_dir()
    # 此时 output_path 一定存在，且是文件夹或 zip 压缩包（零大小）

    return input_path, output_path


def get_config() -> Config:
    input_path, output_path = None, None
    while input_path is None or output_path is None:
        input_path, output_path = get_input_output()

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

    concurrency = inquirer.text(
        message="并行数:",
        default="max",
    ).execute() if ("concurrency" not in preset) else preset["concurrency"]
    config.concurrency = parse_concurrency(concurrency)

    return config


def get_image_list(config: Config) -> list[Path]:
    directory = config.input_path
    if config.input_path.is_file():
        assert config.input_path.suffix.lower() == ".zip"
        color_print([("green", "[*] 解压中...")])
        config.input_tmp_path = unzip_to_tmp(config.input_path)
        color_print([("green", "[*] 解压完成")])
        directory = config.input_tmp_path

    color_print([("green", "[*] 遍历文件夹中...")])
    img_list = list_all_files(directory)
    color_print([("green", "[*] 遍历完成: "), ("yellow", f"共 {len(img_list)} 个文件")])

    color_print([("green", "[*] 过滤非图片...")])
    img_list = filter_images(img_list)
    color_print([("green", "[*] 过滤完成: "), ("yellow", f"共 {len(img_list)} 个图片")])

    return img_list


def start_process(config: Config, img_list: list[Path]) -> None:
    if config.output_path.is_file():
        assert config.output_path.suffix.lower() == ".zip"
        config.output_tmp_path = Path(tempfile.mkdtemp())

    color_print([("green", "[*] 生成任务...")])
    tasks = prepare_resample_tasks(config, img_list)
    color_print([("green", "[*] 开始任务...")])
    err = execute_tasks(config, tasks)
    color_print([("green", "[*] 处理完成")])

    for i, e in enumerate(err):  # 打印错误信息
        color_print([("red", f"[x] #{i} {e}")])


def make_zip_result(config: Config) -> None:
    color_print([("green", "[*] 压缩中...")])
    make_zip(config.output_path, config.output_tmp_path)
    color_print([("green", "[*] 压缩完成")])


def cleanup(config: Config) -> None:
    color_print([("green", "[*] 清理中...")])
    if (config.input_tmp_path is not None and
            inquirer.confirm(message=f"确认删除{config.input_tmp_path}?", default=True).execute()):
        shutil.rmtree(config.input_tmp_path)
    if (config.output_tmp_path is not None and
            inquirer.confirm(message=f"确认删除{config.output_tmp_path}?", default=True).execute()):
        shutil.rmtree(config.output_tmp_path)
    color_print([("green", "[*] 清理完成")])


def main() -> None:
    print_header(cls=True)
    config: Config = get_config()
    img_list = get_image_list(config)

    if not inquirer.confirm(message="确认开始处理吗?", default=True).execute():
        return

    print_header(cls=True)
    start_process(config, img_list)

    if config.output_path.is_file():
        make_zip_result(config)

    cleanup(config)

    if not inquirer.confirm(message="是否继续?", default=False).execute():
        exit(0)


if __name__ == '__main__':
    while True:
        main()
