from models.vk_event import VkObject


class Block(VkObject):
    admin_id: int
    user_id: int
    unblock_date: int

    def __init__(self, admin_id, user_id, unblock_date, *args, **kwargs):
        self.admin_id = admin_id
        self.user_id = user_id
        self.unblock_date = unblock_date

        super().__init__(*args, **kwargs)


class Unblock(VkObject):
    admin_id: int
    user_id: int
    by_end_date: int

    def __init__(self, admin_id, user_id, by_end_date, *args, **kwargs):
        self.admin_id = admin_id
        self.user_id = user_id
        self.by_end_date = by_end_date

        super().__init__(*args, **kwargs)
