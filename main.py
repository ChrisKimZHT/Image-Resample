import os
import threading
from PIL import Image

sem = threading.Semaphore(8)
ext_list = [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff", ".webp"]


def get_filepath(dir_path: str, res_list: list) -> list:
    for file in os.listdir(dir_path):
        file_path = os.path.join(dir_path, file)
        if os.path.isdir(file_path):
            get_filepath(file_path, res_list)
        else:
            res_list.append(file_path)
    return res_list


def resample_img(img_path: str, save_path: str, limit: int = 2400, quality: int = 100) -> None:
    with sem:
        img = Image.open(img_path)
        width, height = img.size
        if width > height and width > limit:
            img = img.resize((limit, int(limit / width * height)))
        elif width <= height and height > limit:
            img = img.resize((int(limit / height * width), limit))
        img.save(save_path, quality=quality)
        print(f"[ ] 已处理: {img_path}")


def main() -> None:
    input_path = input("输入文件夹: ")
    output_path = input("输出文件夹: ")
    img_list = get_filepath(input_path, [])
    for img_path in img_list:
        path, file_and_ext = os.path.split(img_path)
        file, ext = os.path.splitext(file_and_ext)
        if ext.lower() in ext_list:
            new_path = path.replace(input_path, output_path)
            save_path = new_path + "\\" + file + ext
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            threading.Thread(target=resample_img, args=(img_path, save_path)).start()
        else:
            print(f"[!] 已跳过: {img_path}")


if __name__ == '__main__':
    main()
