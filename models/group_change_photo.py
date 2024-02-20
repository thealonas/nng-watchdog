from models.vk_event import VkObject


class GroupChangePhoto(VkObject):
    user_id: int
    photo: dict

    def __init__(self, user_id, photo, *data, **kwargs):
        self.user_id = user_id
        self.photo = photo

        super().__init__(*data, **kwargs)
