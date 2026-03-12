from dataclasses import dataclass, asdict
from typing import List, Optional


@dataclass
class FileMetadata:
    name: str
    file_path: str
    language: str
    body: bytes
    hash: str
    package: Optional[str]
    imports: Optional[list[str]]
