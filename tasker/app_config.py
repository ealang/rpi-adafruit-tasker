import dataclasses
from typing import List


@dataclasses.dataclass
class AppConfig:
    display_name: str
    binary: str
    args: List[str]
    retry_count: int = 5
    retry_delay: float = 2
