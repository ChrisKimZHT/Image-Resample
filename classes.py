from dataclasses import dataclass

from InquirerPy.validator import PathValidator


@dataclass
class Config:
    input_path: str = ""
    output_path: str = ""
    img_size: int = 2400
    img_format: str = "jpg"
    img_quality: int = -1  # quality = -1 特指 png 格式
    keep_alpha: bool = False
    concurrency: int = 8
    zip: bool = False


class PathValidatorWithoutQuote(PathValidator):
    def validate(self, document) -> None:
        document._text = document.text.strip("\"").strip("\'")
        super().validate(document)
