from models.vk_event import VkObject


class GroupLeave(VkObject):
    user_id: int
    self: int

    def __init__(self, user_id, if_self, *args, **kwargs):
        self.user_id = user_id
        self.self = if_self

        super().__init__(*args, **kwargs)
