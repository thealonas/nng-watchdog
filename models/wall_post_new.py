from models.vk_event import VkObject


class Wall(VkObject):
    id: int
    owner_id: int
    from_id: int
    created_by: int | None

    def __init__(self, id, owner_id, from_id, created_by=None, *args, **kwargs):
        self.id = id
        self.owner_id = owner_id
        self.from_id = from_id
        self.created_by = created_by

        super().__init__(*args, **kwargs)
