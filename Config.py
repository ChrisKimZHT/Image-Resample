from dataclasses import dataclass


@dataclass
class Config:
    input_path: str
    output_path: str
    img_size: int
    img_format: str
    img_quality: int
    keep_alpha: bool
    concurrency: int
