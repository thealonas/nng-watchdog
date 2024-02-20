import json
import os
import sys
import traceback

import sentry_sdk
import websocket
from nng_sdk.api.api import NngApi
from nng_sdk.vk.vk_manager import VkManager
from websocket import WebSocketApp

from actions.ban import BanService
from actions.group import GroupService
from actions.wall import WallService
from logger import get_logger
from models.block import Block, Unblock
from models.group_change_photo import GroupChangePhoto
from models.group_leave import GroupLeave
from models.vk_event import VkEvent
from models.wall_post_new import Wall

sentry_sdk.init(
    dsn="https://5fd48a7c43dad54e5af351b08a519e6f@o555933.ingest.sentry.io/4505851345043456",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)

logger = get_logger()

api = NngApi("watchdog", os.environ.get("NNG_API_AK"))

url = str(os.environ.get("NNG_API_URL"))

ban = BanService(api)
groups = GroupService(api)
wall = WallService(api)

crash = False


def raw_websocket_url():
    return (
        url.replace("http://", "ws://").replace("https://", "wss://") + "/callback/logs"
    )


def auth_websocket_url():
    return raw_websocket_url() + "?token=" + api.token


# noinspection PyTypeChecker
def event_router(event_dict: dict):
    event = VkEvent.from_dict(event_dict)
    logger.info(f"пришел ивент {event.type}")
    match event.type:
        case "wall_repost" | "wall_post_new":
            wall.wall_new(Wall(**event.object), event)
        case "user_block":
            ban.user_block(Block(**event.object), event)
        case "user_unblock":
            ban.user_unblock(Unblock(**event.object), event)
        case "group_leave":
            groups.group_leave(
                GroupLeave(event.object["user_id"], event.object["self"]), event
            )
        case "group_change_photo":
            groups.group_change_photo(GroupChangePhoto(**event.object), event)
        case _:
            logger.info(f"неизвестный ивент {event.type}")


def on_message(socket: WebSocketApp, message):
    try:
        event_router(json.loads(message))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        print(traceback.print_exc())


def on_error(socket: WebSocketApp, error):
    logger.error(f"произошла ошибка: {error}")


def on_close(socket: WebSocketApp, close_status_code, close_msg):
    sys.exit(f"соедениние с было закрыто со статусом {close_status_code}: {close_msg}")


def on_open(socket: WebSocketApp):
    logger.info(f"открыл соеденение c {raw_websocket_url()} cлушаю ивенты...")


if __name__ == "__main__":
    VkManager().auth_in_vk()
    ws = websocket.WebSocketApp(
        auth_websocket_url(),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.on_open = on_open

    ws.run_forever()

    while True:
        input()
