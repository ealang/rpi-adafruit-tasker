from dataclasses import dataclass
from typing import List


@dataclass
class ProgramConfig:
    display_name: str
    binary: str
    args: List[str]



@dataclass
class DaemonConfig(ProgramConfig):
    retry_count: int = 5
    retry_delay: float = 2

AppConfig = DaemonConfig

@dataclass
class TaskerConfig:
    mutex_daemons: List[DaemonConfig]
    tasks: List[ProgramConfig]
