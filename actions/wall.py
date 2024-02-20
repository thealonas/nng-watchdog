import datetime

from nng_sdk.api.watchdog_category import PutWatchdog
from nng_sdk.pydantic_models.user import BanPriority, Violation, ViolationType
from nng_sdk.vk.actions import delete_post

from actions.base import BaseWatchdogService
from models.vk_event import VkEvent
from models.wall_post_new import Wall


class WallService(BaseWatchdogService):
    def wall_new(self, wall: Wall, event: VkEvent):
        log = PutWatchdog(
            group_id=event.group_id,
            priority=BanPriority.green,
            date=datetime.date.today(),
        )

        if not wall.created_by:
            self.logger.warning(
                f"не могу обработать {event.type}, отсутствует created_by"
            )
            self.api.watchdog.add_watchdog_log(log)
            return

        intruder = wall.created_by

        if wall.created_by == 100:
            self.logger.warning("пост от вк")
            return

        user = self.get_user(intruder)

        if user.admin:
            self.logger.info(f"ивент {event.type} санкционирован")
            return

        log.intruder = intruder
        log.reviewed = True

        delete_post(event.group_id, wall.id)

        new_watchdog = self.api.watchdog.add_watchdog_log(log)

        self.ban_user_in_api_and_group(
            user,
            Violation(
                type=ViolationType.banned,
                group_id=event.group_id,
                priority=BanPriority.green,
                active=True,
                date=datetime.date.today(),
                watchdog_ref=new_watchdog.watchdog_id,
            ),
            event.group_id,
        )

        self.logger.info(f"пользователь id{user.user_id} был забанен за {event.type}")
