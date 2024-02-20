from logging import Logger

from nng_sdk.api.api import NngApi
from nng_sdk.api.watchdog_category import WatchdogWebsocketLog, WatchdogWebsocketLogType
from nng_sdk.pydantic_models.user import User, Violation, BanPriority, ViolationType
from nng_sdk.vk.actions import ban_editor
from requests import HTTPError

from logger import get_logger


class BaseWatchdogService:
    logger: Logger
    api: NngApi

    def __init__(self, api: NngApi):
        self.logger = get_logger()
        self.api = api

    def get_user(self, user_id: int, force: bool = True) -> User:
        if user_id == 100:
            raise RuntimeError("Cannot get user 100")

        try:
            return self.api.users.get_user(user_id)
        except HTTPError as e:
            if force and e.response.status_code == 404:
                self.api.users.add_user(user_id)
                return self.api.users.get_user(user_id)
            raise

    @staticmethod
    def __is_valid_green(violation: Violation):
        if (
            violation.type != ViolationType.warned
            or violation.priority != BanPriority.green
        ):
            return False

        return not violation.is_expired()

    def __green_ban(self, user: User, violation: Violation, group_id: int):
        if len([i for i in user.violations if self.__is_valid_green(i)]) < 2:
            violation.type = ViolationType.warned
            violation.active = None
            self.api.users.add_violation(user.user_id, violation)
            self.api.watchdog.notify_watchdog_log(
                WatchdogWebsocketLog(
                    type=WatchdogWebsocketLogType.new_warning,
                    priority=BanPriority.green,
                    group=group_id,
                    send_to_user=user.user_id,
                )
            )
            return

        ban_editor(group_id, user.user_id)

        violation.type = ViolationType.banned
        violation.active = True

        self.api.users.add_violation(user.user_id, violation)
        self.api.watchdog.notify_watchdog_log(
            WatchdogWebsocketLog(
                type=WatchdogWebsocketLogType.new_ban,
                send_to_user=user.user_id,
                group=group_id,
                priority=BanPriority.green,
            )
        )

    def ban_user_in_api_and_group(
        self, user: User, violation: Violation, group_id: int
    ):
        if violation.priority == BanPriority.green:
            return self.__green_ban(user, violation, group_id)

        ban_editor(group_id, user.user_id)
        self.api.users.add_violation(user.user_id, violation)
        self.api.watchdog.notify_watchdog_log(
            WatchdogWebsocketLog(
                type=WatchdogWebsocketLogType.new_ban,
                send_to_user=user.user_id,
                group=group_id,
                priority=violation.priority,
            )
        )

    def is_admin(self, user_id: int) -> bool:
        return self.api.users.get_user(user_id).admin
