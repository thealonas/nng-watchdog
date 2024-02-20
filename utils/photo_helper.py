import json

import requests
from nng_sdk.vk.actions import get_photo_upload_server, save_owner_photo, delete_post


class PhotoHelper:
    @staticmethod
    def __download_photo() -> bytes:
        photo_url = "https://nng.alonas.lv/img/style/logo/png/editors.png"
        response = requests.get(photo_url)
        response.raise_for_status()
        return response.content

    @staticmethod
    def __form_content(file, file_extension):
        form_data = {"file": (f"file.{file_extension}", file)}
        return form_data

    @staticmethod
    def __post_and_return_response(server_url, data, files):
        response = requests.post(server_url, data=data, files=files)
        response.raise_for_status()
        return response.text

    @staticmethod
    def __upload_file(server_url, file, file_extension, x, y, w):
        form_data = {"file": (f"file.{file_extension}", file)}
        data = {"_square_crop": f"{x},{y},{w}"}
        return PhotoHelper.__post_and_return_response(server_url, data, form_data)

    @staticmethod
    def __get_upload_server(group: int):
        return get_photo_upload_server(-group)

    @staticmethod
    def set_avatar(group: int):
        file: bytes = PhotoHelper.__download_photo()
        server_url = PhotoHelper.__get_upload_server(group)
        photo_result = json.loads(
            PhotoHelper.__upload_file(server_url, file, "png", 5000, 5000, 5000)
        )
        hash_value = photo_result.get("hash")
        photo = photo_result.get("photo")
        server = photo_result.get("server")

        if not hash_value or not photo or not server:
            raise ValueError("Missing required data in photo upload response")

        photo_save_result = save_owner_photo(hash_value, photo, server)
        delete_post(group, photo_save_result.get("post_id"))
