import datetime

import sentry_sdk
from nng_sdk.api.watchdog_category import PutWatchdog
from nng_sdk.pydantic_models.user import BanPriority, Violation, ViolationType
from nng_sdk.vk.actions import delete_photo, vk_action
from nng_sdk.vk.vk_manager import VkManager

from actions.base import BaseWatchdogService
from models.group_change_photo import GroupChangePhoto
from models.group_leave import GroupLeave
from models.vk_event import VkEvent
from utils.photo_helper import PhotoHelper


class GroupService(BaseWatchdogService):
    vk_manager = VkManager()

    def group_leave(self, group_leave: GroupLeave, event: VkEvent):
        if group_leave.self == 1:  # если вышел сам
            return

        # нужно чтобы не репортило если вач банит сам
        if self.get_user(
            group_leave.user_id
        ).has_active_violation():  # если есть блокировка
            return

        self.api.watchdog.add_watchdog_log(
            PutWatchdog(
                victim=group_leave.user_id,
                group_id=event.group_id,
                priority=BanPriority.orange,
                date=datetime.date.today(),
            )
        )

    @vk_action
    def _get_all_photos(self, group_id: int) -> list[dict]:
        return self.vk_manager.api.photos.getAll(owner_id=-group_id, count=200).get(
            "items"
        )

    @staticmethod
    def _delete_all_photos(group_id: int, all_photos: list[dict]):
        for photo in all_photos:
            photo_id = photo.get("id")
            if not photo_id:
                sentry_sdk.capture_exception(RuntimeError(f"No id in photo"))
                continue
            delete_photo(group_id, photo_id)

    def group_change_photo(self, change_photo: GroupChangePhoto, event: VkEvent):
        log = PutWatchdog(
            group_id=event.group_id,
            priority=BanPriority.orange,
            date=datetime.date.today(),
        )

        if not change_photo.photo:
            self.logger.warning(f"нельзя обработать {event.type}, отсутствует photo")
            return

        if not change_photo.user_id or change_photo.user_id == 100:
            self.logger.warning(f"нельзя обработать {event.type}, отсутствует user_id")
            self.api.watchdog.add_watchdog_log(log)
            return

        photo_id = change_photo.photo["id"]

        user = self.get_user(change_photo.user_id)

        if user.admin:
            self.logger.info(f"ивент {event.type} санкционирован")
            return

        log.intruder = user.user_id
        log.reviewed = True

        new_watchdog = self.api.watchdog.add_watchdog_log(log)

        self.ban_user_in_api_and_group(
            user,
            Violation(
                type=ViolationType.banned,
                group_id=event.group_id,
                priority=BanPriority.orange,
                active=True,
                date=datetime.date.today(),
                watchdog_ref=new_watchdog.watchdog_id,
            ),
            event.group_id,
        )

        self.logger.info(f"id{user.user_id} был забанен за {event.type}")

        all_photos: list[dict] = self._get_all_photos(event.group_id)
        if len(all_photos) == 0:
            self.logger.info(
                f"в группе {event.group_id} нет фото, устанавливаю новый аватар"
            )
            PhotoHelper.set_avatar(event.group_id)

        elif len(all_photos) == 2:
            self.logger.info(
                f"всего две фото, удаляю загруженное {photo_id} из группы {event.group_id}"
            )
            delete_photo(event.group_id, photo_id)

        else:
            self.logger.info(f"удаляю все фотографии из группы {event.group_id}")
            self._delete_all_photos(event.group_id, all_photos)
            self.logger.info(f"устанавливаю новый аватар")
            PhotoHelper.set_avatar(event.group_id)
