from dataclasses import dataclass, asdict
from typing import Optional
import json
import base64

@dataclass
class StructuralSymbol:
    id: str
    type: str
    name: str
    symbol_path: str
    parent_id: Optional[str]
    file_path: str
    body: bytes
    start_line: int
    end_line: int
    metadata: dict
    
    def to_json(self):
        d = asdict(self)
        d["body"] = self.body.decode("utf-8")
        return json.dumps(d)

    @staticmethod
    def from_json(s: str):
        d = json.loads(s)
        d["body"] = d["body"].encode("utf-8")
        return StructuralSymbol(**d)
    
    def __str__(self):
        o = asdict(self)
        del o["body"]
        return f"{json.dumps(o, indent=True)}"
