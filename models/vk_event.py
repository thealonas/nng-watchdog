from typing import Optional, Any

from pydantic import BaseModel


class VkEvent(BaseModel):
    group_id: int
    type: str
    secret: Optional[str]
    object: Optional[Any]

    @staticmethod
    def from_dict(data: dict) -> "VkEvent":
        return VkEvent(
            group_id=data["group_id"],
            type=data["type"],
            secret=data.get("secret"),
            object=data.get("object"),
        )


class VkObject(object):
    def __init__(self, *args, **kwargs):
        pass
