import json
import os
import re
from urllib.request import Request, urlopen

import jsonpath

from netease_music_tool.config import ssl_ctx


def extract_song_id(raw_str):
    match = re.search(r'id=(\d+)', raw_str)
    if match:
        return match.group(1)
    return raw_str.strip()


def parse_song_ids(raw_text):
    raw_lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    return [extract_song_id(line) for line in raw_lines]


def fetch_song_info(song_ids):
    song_info_list = []
    for data_id in song_ids:
        try:
            url = f'https://music.163.com/api/song/enhance/player/url?id={data_id}&ids=[{data_id}]&br=3200000'
            req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
            response = urlopen(req, timeout=15, context=ssl_ctx)
            html = response.read()
            res_json = json.loads(html)
            dataurl = jsonpath.jsonpath(res_json, "$..url")

            if not dataurl or dataurl == [None]:
                song_info_list.append({
                    "id": str(data_id),
                    "ok": False,
                    "url": None,
                    "size": 0,
                })
                continue

            audio_url = ''.join(dataurl)
            size_list = jsonpath.jsonpath(res_json, "$..size")
            size_val = size_list[0] if size_list else 0
            size_mb = round(size_val / 1024 / 1024, 2)

            song_info_list.append({
                "id": str(data_id),
                "ok": True,
                "url": audio_url,
                "size": size_val,
                "size_text": f"{size_mb} MB",
            })
        except Exception as exc:
            print(f"[DEBUG] ID:{data_id} 请求异常: {exc}")
            song_info_list.append({
                "id": str(data_id),
                "ok": False,
                "url": None,
                "size": 0,
                "error": str(exc),
            })
    return song_info_list


def download_audio_by_info(info, save_dir, set_status=None):
    if not info or not info.get("ok") or not info.get("url"):
        return False

    try:
        if set_status:
            set_status(f"正在下载 ID:{info['id']}")
        req_audio = Request(info["url"], headers={"User-Agent": "Mozilla/5.0"})
        audio_data = urlopen(req_audio, timeout=30, context=ssl_ctx).read()
        save_file = os.path.join(save_dir, f"{info['id']}.mp3")
        with open(save_file, "wb") as file_handle:
            file_handle.write(audio_data)
        return True
    except Exception as exc:
        print(f"[DEBUG] ID:{info['id']}下载异常:{exc}")
        return False
