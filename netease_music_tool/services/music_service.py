import base64
import binascii
import json
import os
import re
import struct
from urllib.request import Request, urlopen

from typing import Iterable

from Crypto.Cipher import AES
import jsonpath
from mutagen.flac import FLAC, Picture
from mutagen.id3 import APIC, TALB, TIT2, TPE1, ID3, ID3NoHeaderError
from mutagen.mp3 import MP3

from netease_music_tool.config import ssl_ctx
from netease_music_tool.utils.ncm import meta_key_bytes, unpad_bytes


def extract_song_id(raw_str):
    match = re.search(r'id=(\d+)', raw_str)
    if match:
        return match.group(1)
    return raw_str.strip()


def sanitize_file_name_part(value):
    if value is None:
        return "未知"
    cleaned = str(value).strip().replace("/", " ").replace("\\", " ")
    cleaned = re.sub(r"[\\/:*?\"<>|]", "", cleaned)
    cleaned = cleaned.replace("\x00", "").strip(". ")
    return cleaned or "未知"


def coerce_artist_names(artists):
    """把各种形态的歌手字段拍平成歌手名列表。

    NCM 元数据里 artist 通常形如 [["歌手名", "歌手ID"], ...]，内层第一项才是名字，
    因此对嵌套列表只取第一个非空字符串，避免把歌手 ID 当名字写入标签。
    """
    if not artists:
        return []
    names = []
    for artist in artists:
        if isinstance(artist, str):
            cleaned = artist.strip()
            if cleaned:
                names.append(cleaned)
        elif isinstance(artist, (list, tuple)):
            for name in artist:
                if isinstance(name, str) and name.strip():
                    names.append(name.strip())
                    break
    return names


def build_output_audio_name(metadata, fallback_base=None):
    title = metadata.get("musicName") or fallback_base or "未知歌曲"
    artist_names = coerce_artist_names(metadata.get("artist") or [])
    artist = artist_names[0] if artist_names else ""
    extension = str(metadata.get("format") or "mp3").lower().lstrip(".")
    safe_title = sanitize_file_name_part(title)
    if not artist:
        return f"{safe_title}.{extension}"
    safe_artist = sanitize_file_name_part(artist)
    if safe_title and safe_artist and safe_title.lower() != safe_artist.lower():
        return f"{safe_title}-{safe_artist}.{extension}"
    return f"{safe_title}.{extension}"


def format_duration(seconds):
    if seconds is None:
        return "00:00"
    try:
        total_seconds = float(seconds)
    except (TypeError, ValueError):
        return "00:00"
    if total_seconds < 0:
        total_seconds = 0
    total_seconds = int(total_seconds)
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


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


def parse_mv_detail(data):
    """从 /api/mv/detail 的响应中提取 MV 展示信息，自动选取最高可用清晰度。"""
    detail = data.get("data") or {}
    name = detail.get("name") or "未知MV"
    artist = detail.get("artistName") or ""
    brs = detail.get("brs") or {}
    url = next((brs[quality] for quality in ("1080", "720", "480", "240") if brs.get(quality)), None)
    duration = detail.get("duration")
    return {
        "id": str(detail.get("id") or ""),
        "name": name,
        "artist": artist,
        "duration": duration,
        "duration_text": format_duration(duration / 1000 if duration else None),
        "url": url,
        "ok": bool(url),
    }


def fetch_mv_info(mv_ids, cookie=""):
    """批量获取 MV 信息，每个条目包含最高清晰度播放地址。"""
    results = []
    for mv_id in mv_ids:
        try:
            url = f"https://music.163.com/api/mv/detail?id={mv_id}"
            headers = {"User-Agent": "Mozilla/5.0", "Referer": "https://music.163.com/"}
            if cookie.strip():
                headers["Cookie"] = cookie.strip()
            req = Request(url, headers=headers)
            res = json.loads(urlopen(req, timeout=15, context=ssl_ctx).read())
            info = parse_mv_detail(res)
            if not info["id"]:
                info["id"] = str(mv_id)
            results.append(info)
        except Exception as exc:
            print(f"[DEBUG] MV:{mv_id} 请求异常: {exc}")
            results.append({"id": str(mv_id), "ok": False, "name": "-", "url": None, "error": str(exc)})
    return results


def download_mv(info, save_dir, set_status=None):
    """按 MV 信息下载 mp4 文件，返回是否成功。"""
    if not info or not info.get("ok") or not info.get("url"):
        return False
    try:
        if set_status:
            set_status(f"正在下载 MV:{info.get('id')} {info.get('name', '')}")
        req = Request(info["url"], headers={"User-Agent": "Mozilla/5.0", "Referer": "https://music.163.com/"})
        mv_data = urlopen(req, timeout=60, context=ssl_ctx).read()
        os.makedirs(save_dir, exist_ok=True)
        save_file = os.path.join(save_dir, f"{info['id']}.mp4")
        with open(save_file, "wb") as file_handle:
            file_handle.write(mv_data)
        return True
    except Exception as exc:
        print(f"[DEBUG] MV:{info.get('id')} 下载异常:{exc}")
        return False


def read_ncm_metadata(file_path):
    """Read display metadata and cover data from an NCM file."""
    with open(file_path, "rb") as file_handle:
        if file_handle.read(8) != b"CTENFDAM":
            raise ValueError("不是有效的 NCM 文件")

        file_handle.seek(2, 1)
        key_length = struct.unpack("<I", file_handle.read(4))[0]
        file_handle.seek(key_length, 1)
        meta_length = struct.unpack("<I", file_handle.read(4))[0]
        meta_data = bytearray(file_handle.read(meta_length))
        for index in range(len(meta_data)):
            meta_data[index] ^= 0x63
        meta_data = base64.b64decode(bytes(meta_data)[22:])
        metadata = json.loads(
            unpad_bytes(AES.new(meta_key_bytes(), AES.MODE_ECB).decrypt(meta_data))[6:].decode("utf-8")
        )

        file_handle.seek(9, 1)
        image_size = struct.unpack("<I", file_handle.read(4))[0]
        image_data = file_handle.read(image_size)

    artist_names = coerce_artist_names(metadata.get("artist") or [])
    duration_ms = metadata.get("duration") or metadata.get("duration_ms")
    duration_value = duration_ms / 1000 if isinstance(duration_ms, (int, float)) and duration_ms else None
    return {
        "title": metadata.get("musicName") or os.path.splitext(os.path.basename(file_path))[0],
        "artist": "、".join(artist_names) or "未知作者",
        "album": metadata.get("album") or "",
        "format": str(metadata.get("format", "")).upper(),
        "cover": image_data,
        "duration": duration_value,
        "duration_text": format_duration(duration_value),
        "source_size": os.path.getsize(file_path),
        "raw": metadata,
    }


def embed_audio_metadata(output_path, metadata, image_data):
    """Embed NCM metadata and cover art into an MP3 or FLAC file."""
    title = metadata.get("musicName", "")
    artist = "、".join(coerce_artist_names(metadata.get("artist") or [])) or "未知作者"
    album = metadata.get("album", "")
    extension = os.path.splitext(output_path)[1].lower()

    if extension == ".mp3":
        try:
            tags = ID3(output_path)
        except ID3NoHeaderError:
            tags = ID3()
        tags.add(TIT2(encoding=3, text=title))
        tags.add(TPE1(encoding=3, text=artist))
        tags.add(TALB(encoding=3, text=album))
        if image_data:
            mime = "image/jpeg" if image_data[:3] == b"\xff\xd8\xff" else "image/png"
            tags.add(APIC(encoding=3, mime=mime, type=3, desc="Cover", data=image_data))
        tags.save(output_path)
        return

    if extension == ".flac":
        audio = FLAC(output_path)
        audio["title"] = title
        audio["artist"] = artist
        audio["album"] = album
        if image_data:
            picture = Picture()
            picture.type = 3
            picture.mime = "image/jpeg" if image_data[:3] == b"\xff\xd8\xff" else "image/png"
            picture.data = image_data
            audio.add_picture(picture)
        audio.save()
        return

    raise ValueError(f"暂不支持将元数据嵌入 {extension[1:].upper()} 音频")


def decrypt_ncm(file_path, output_dir=None, embed_metadata=False):
    """Decrypt an NCM file and return the generated audio path.

    embed_metadata=True 时把元数据（歌名/歌手/专辑）和封面嵌入音频文件；
    否则只输出解码后的原始音频，不再生成任何外置的封面或 JSON 侧车文件。
    输出文件名为「歌曲名-歌手.扩展名」。
    """
    if output_dir is None:
        output_dir = os.path.dirname(file_path)
    os.makedirs(output_dir, exist_ok=True)

    core_key = binascii.a2b_hex("687A4852416D736F356B496E62617857")
    meta_key = binascii.a2b_hex("2331346C6A6B5F215C5D2630553C2728")

    def unpad(data):
        pad_len = data[-1] if isinstance(data[-1], int) else ord(data[-1])
        return data[:-pad_len]

    with open(file_path, "rb") as file_handle:
        if file_handle.read(8) != b"CTENFDAM":
            raise ValueError("不是有效的 NCM 文件")

        file_handle.seek(2, 1)
        key_length = struct.unpack("<I", file_handle.read(4))[0]
        key_data = bytearray(file_handle.read(key_length))
        for index in range(len(key_data)):
            key_data[index] ^= 0x64

        cipher = AES.new(core_key, AES.MODE_ECB)
        key_data = unpad(cipher.decrypt(bytes(key_data)))[17:]
        key_box = bytearray(range(256))
        last_byte = 0
        key_offset = 0
        for index in range(256):
            swap = key_box[index]
            key_offset %= len(key_data)
            last_byte = (swap + last_byte + key_data[key_offset]) & 0xFF
            key_offset += 1
            key_box[index], key_box[last_byte] = key_box[last_byte], swap

        meta_length = struct.unpack("<I", file_handle.read(4))[0]
        meta_data = bytearray(file_handle.read(meta_length))
        for index in range(len(meta_data)):
            meta_data[index] ^= 0x63
        meta_data = base64.b64decode(bytes(meta_data)[22:])
        meta_data = unpad(AES.new(meta_key, AES.MODE_ECB).decrypt(meta_data))[6:]
        metadata = json.loads(meta_data.decode("utf-8"))

        file_handle.seek(9, 1)
        image_size = struct.unpack("<I", file_handle.read(4))[0]
        image_data = file_handle.read(image_size)
        output_name = build_output_audio_name(metadata, os.path.splitext(os.path.basename(file_path))[0])
        output_path = os.path.join(output_dir, output_name)

        with open(output_path, "wb") as output_handle:
            while chunk := bytearray(file_handle.read(0x8000)):
                for index in range(1, len(chunk) + 1):
                    position = index & 0xFF
                    chunk[index - 1] ^= key_box[
                        (key_box[position] + key_box[(key_box[position] + position) & 0xFF]) & 0xFF
                    ]
                output_handle.write(chunk)

    if embed_metadata:
        embed_audio_metadata(output_path, metadata, image_data)

    return output_path
