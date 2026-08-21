import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from netease_music_tool.services.music_service import (
    build_output_audio_name,
    coerce_artist_names,
    decrypt_ncm,
    download_mv,
    extract_song_id,
    parse_mv_detail,
    parse_song_ids,
    read_ncm_metadata,
)


class MusicServiceTests(unittest.TestCase):
    def test_extract_song_id_from_url(self):
        self.assertEqual(extract_song_id("https://music.163.com/#/song?id=1973665667"), "1973665667")

    def test_extract_song_id_from_plain_id(self):
        self.assertEqual(extract_song_id("1294924084"), "1294924084")

    def test_parse_song_ids_ignores_empty_lines(self):
        raw_text = "\nhttps://music.163.com/#/song?id=1973665667\n1294924084\n   \n"
        self.assertEqual(parse_song_ids(raw_text), ["1973665667", "1294924084"])

    def test_build_output_audio_name_uses_song_and_artist(self):
        metadata = {
            "musicName": "夜曲",
            "artist": [["周杰伦"], ["五月天"]],
            "format": "mp3",
        }
        self.assertEqual(build_output_audio_name(metadata), "夜曲-周杰伦.mp3")

    def test_build_output_audio_name_falls_back_to_plain_name(self):
        metadata = {"musicName": "My Song", "format": "flac"}
        self.assertEqual(build_output_audio_name(metadata), "My Song.flac")

    def test_parse_mv_detail_picks_highest_quality(self):
        data = {
            "data": {
                "id": 123,
                "name": "Some MV",
                "artistName": "Artist",
                "duration": 249000,
                "brs": {"240": "low.mp4", "720": "high.mp4"},
            }
        }
        info = parse_mv_detail(data)
        self.assertTrue(info["ok"])
        self.assertEqual(info["id"], "123")
        self.assertEqual(info["name"], "Some MV")
        self.assertEqual(info["artist"], "Artist")
        self.assertEqual(info["duration_text"], "04:09")
        self.assertEqual(info["url"], "high.mp4")

    def test_parse_mv_detail_handles_empty_brs(self):
        info = parse_mv_detail({"data": {"id": 456, "brs": {}}})
        self.assertFalse(info["ok"])
        self.assertIsNone(info["url"])

    def test_download_mv_without_url_returns_false(self):
        self.assertFalse(download_mv({"id": "1", "ok": True, "url": None}, "some_dir"))
        self.assertFalse(download_mv({"id": "1", "ok": False, "url": "http://x"}, "some_dir"))
        self.assertFalse(download_mv(None, "some_dir"))

    def test_coerce_artist_names_skips_artist_id(self):
        self.assertEqual(coerce_artist_names([["Chris James", "145038"]]), ["Chris James"])
        self.assertEqual(coerce_artist_names([["周杰伦"], ["五月天"]]), ["周杰伦", "五月天"])
        self.assertEqual(coerce_artist_names(["周杰伦"]), ["周杰伦"])

    @unittest.skipUnless(os.path.exists("test.ncm"), "缺少 test.ncm 测试样本")
    def test_read_ncm_metadata_duration_is_ms(self):
        meta = read_ncm_metadata("test.ncm")
        self.assertEqual(meta["duration_text"], "02:28")
        self.assertEqual(meta["artist"], "Chris James")

    def test_decrypt_ncm_rejects_invalid_header(self):
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.ncm"
            file_path.write_bytes(b"invalid")
            with self.assertRaisesRegex(ValueError, "不是有效的 NCM 文件"):
                decrypt_ncm(str(file_path), temp_dir)


if __name__ == "__main__":
    unittest.main()
