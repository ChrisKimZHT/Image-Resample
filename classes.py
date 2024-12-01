from dataclasses import dataclass

from InquirerPy.validator import PathValidator


@dataclass
class Config:
    input_path: str
    output_path: str
    img_size: int
    img_format: str
    img_quality: int
    keep_alpha: bool
    concurrency: int


class PathValidatorWithoutQuote(PathValidator):
    def validate(self, document) -> None:
        document._text = document.text.strip("\"").strip("\'")
        super().validate(document)
