import unittest

from netease_music_tool.services.music_service import extract_song_id, parse_song_ids


class MusicServiceTests(unittest.TestCase):
    def test_extract_song_id_from_url(self):
        self.assertEqual(extract_song_id("https://music.163.com/#/song?id=1973665667"), "1973665667")

    def test_extract_song_id_from_plain_id(self):
        self.assertEqual(extract_song_id("1294924084"), "1294924084")

    def test_parse_song_ids_ignores_empty_lines(self):
        raw_text = "\nhttps://music.163.com/#/song?id=1973665667\n1294924084\n   \n"
        self.assertEqual(parse_song_ids(raw_text), ["1973665667", "1294924084"])


if __name__ == "__main__":
    unittest.main()
