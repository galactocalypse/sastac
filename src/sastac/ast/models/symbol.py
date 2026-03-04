from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class StructuralSymbol:
    id: str
    type: str
    name: str
    parent_id: Optional[str]
    body: bytes
    start_line: Optional[int]
    end_line: Optional[int]
    metadata: dict
    
    def __str__(self):
        return f"""Symbol "{self.type}": {self.name}
    Id: {self.id}
    Parent ID: {self.parent_id}
    Lines: {self.start_line} - {self.end_line}
    Size: {len(self.body)}
    Metadata:
{json.dumps(self.metadata, indent=True)}
    
            """
