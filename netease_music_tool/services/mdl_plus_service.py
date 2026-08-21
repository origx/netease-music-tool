import hashlib
import json
import os

import requests
from Crypto.Cipher import AES


class NeteaseEAPIClient:
    EAPI_KEY = b"e82ckenh8dichen8"

    def __init__(self, cookie=""):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/120.0.0.0 Mobile Safari/537.36",
            "Referer": "https://music.163.com/",
        })
        if cookie.strip():
            self.session.headers["Cookie"] = cookie.strip()

    @staticmethod
    def _pkcs7_pad(data):
        padding = 16 - len(data) % 16
        return data + bytes([padding]) * padding

    def eapi_encrypt(self, path, params):
        text = json.dumps(params, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.md5(f"nobody{path}use{text}md5forencrypt".encode()).hexdigest()
        raw = f"{path}-36cd479b6b5-{text}-36cd479b6b5-{digest}"
        return AES.new(self.EAPI_KEY, AES.MODE_ECB).encrypt(
            self._pkcs7_pad(raw.encode())
        ).hex().upper()

    def request(self, path, params):
        response = self.session.post(
            f"https://interface.music.163.com/eapi{path}",
            data={"params": self.eapi_encrypt(path, params)},
            timeout=25,
        )
        response.raise_for_status()
        return response.json()


def fetch_plus_song_info(song_ids, cookie=""):
    client = NeteaseEAPIClient(cookie)
    results = []
    for song_id in song_ids:
        try:
            result = client.request("/api/song/enhance/player/url", {
                "ids": f"[{song_id}]",
                "br": 3200000,
                "csrf_token": "",
            })
            item = (result.get("data") or [{}])[0]
            audio_url = item.get("url")
            size = item.get("size") or 0
            error_code = item.get("code") or result.get("code")
            results.append({
                "id": str(song_id),
                "ok": bool(audio_url),
                "url": audio_url,
                "size": size,
                "size_text": f"{size / 1024 / 1024:.2f} MB" if size else "-",
                "error_code": error_code,
                "error_message": item.get("message") or result.get("message"),
            })
        except Exception as exc:
            results.append({"id": str(song_id), "ok": False, "url": None, "size": 0, "error": str(exc)})
    return results


def download_plus_audio(info, save_dir, cookie="", set_status=None):
    if not info.get("ok") or not info.get("url"):
        return False
    try:
        if set_status:
            set_status(f"正在下载 ID:{info['id']}")
        response = requests.get(info["url"], headers={"Cookie": cookie} if cookie.strip() else {}, timeout=30)
        response.raise_for_status()
        os.makedirs(save_dir, exist_ok=True)
        with open(os.path.join(save_dir, f"{info['id']}.mp3"), "wb") as output:
            output.write(response.content)
        return True
    except Exception:
        return False
