from dataclasses import dataclass, field
from typing import List

@dataclass
class EmailMessageModel:
    sender: str
    receiver: str
    subject: str
    body: str
    attachments: List[object] = field(default_factory=list)
