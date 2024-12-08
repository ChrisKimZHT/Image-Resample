from dataclasses import dataclass
from pathlib import Path

from InquirerPy.validator import PathValidator


@dataclass
class Config:
    input_path: Path = Path()
    output_path: Path = Path()
    img_size: int = 2400
    img_format: str = "jpg"
    img_quality: int = -1  # quality = -1 特指 png 格式
    keep_alpha: bool = False
    concurrency: int = 8


class PathValidatorWithoutQuote(PathValidator):
    def validate(self, document) -> None:
        """注意，该验证器强制修改了私有变量_text，因此输出时也不会带引号"""
        document._text = document.text.strip("\"").strip("\'")
        super().validate(document)
