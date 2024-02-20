import datetime

from actions.base import BaseWatchdogService
from models.block import Block, Unblock
from models.vk_event import VkEvent
from nng_sdk.api.watchdog_category import PutWatchdog
from nng_sdk.pydantic_models.user import Violation, ViolationType, BanPriority
from nng_sdk.vk.actions import ban_editor, unban_users


class BanService(BaseWatchdogService):
    def user_block(self, block: Block, event: VkEvent):
        if block.admin_id == 100:
            self.logger.warning(f"нельзя обработать {event.type}")
            return

        intruder = self.get_user(block.admin_id)
        victim = self.get_user(block.user_id)

        if intruder.admin:
            self.logger.info(f"ивент {event.type} санкционирован")
            return

        if victim.has_active_violation():
            ban_editor(event.group_id, victim.user_id)
        else:
            unban_users([victim.user_id], event.group_id)

        new_log = self.api.watchdog.add_watchdog_log(
            PutWatchdog(
                intruder=intruder.user_id,
                victim=victim.user_id,
                group_id=event.group_id,
                priority=BanPriority.red,
                date=datetime.date.today(),
                reviewed=True,
            )
        )

        self.ban_user_in_api_and_group(
            intruder,
            Violation(
                type=ViolationType.banned,
                group_id=event.group_id,
                priority=BanPriority.red,
                active=True,
                date=datetime.date.today(),
                watchdog_ref=new_log.watchdog_id,
            ),
            event.group_id,
        )

    def user_unblock(self, unblock: Unblock, event: VkEvent):
        if unblock.admin_id == 100:
            self.logger.warning(f"нельзя обработать {event.type}")
            return

        intruder = self.get_user(unblock.admin_id)

        victim = None
        try:
            victim = self.get_user(unblock.user_id)
        except RuntimeError:
            pass

        if intruder.admin:
            self.logger.info(f"ивент {event.type} санкционирован")
            return

        if not victim or not victim.has_active_violation():
            unban_users([unblock.user_id], event.group_id)
        elif victim.has_active_violation():
            ban_editor(event.group_id, victim.user_id)

        new_log = self.api.watchdog.add_watchdog_log(
            PutWatchdog(
                intruder=intruder.user_id,
                victim=victim.user_id,
                group_id=event.group_id,
                priority=BanPriority.red,
                date=datetime.date.today(),
                reviewed=True,
            )
        )

        self.ban_user_in_api_and_group(
            intruder,
            Violation(
                type=ViolationType.banned,
                group_id=event.group_id,
                priority=BanPriority.red,
                active=True,
                date=datetime.date.today(),
                watchdog_ref=new_log.watchdog_id,
            ),
            event.group_id,
        )
