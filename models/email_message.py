from dataclasses import dataclass, field


@dataclass
class EmailMessageModel:
    sender: str
    receiver: str
    subject: str
    body: str
    attachments: list[object] = field(default_factory=list)
