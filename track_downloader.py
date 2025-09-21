import os
import sys
import csv
import requests
import re
import yt_dlp
from configparser import ConfigParser
from mutagen.easymp4 import EasyMP4
from mutagen.mp4 import MP4, MP4Cover


def safe_filename(s: str, max_length: int = 255) -> str:
    """Sanitize a string making it safe to use as a filename.

    This function was based off the limitations outlined here:
    https://en.wikipedia.org/wiki/Filename.

    :param str s:
        A string to make safe for use as a file name.
    :param int max_length:
        The maximum filename character length.
    :rtype: str
    :returns:
        A sanitized string.
    """
    # Characters in range 0-31 (0x00-0x1F) are not allowed in ntfs filenames.
    ntfs_characters = [chr(i) for i in range(0, 31)]
    characters = [
        r'"',
        r"\#",
        r"\$",
        r"\%",
        r"'",
        r"\*",
        r"\,",
        r"\.",
        r"\/",
        r"\:",
        r'"',
        r"\;",
        r"\<",
        r"\>",
        r"\?",
        r"\\",
        r"\^",
        r"\|",
        r"\~",
        r"\\\\",
    ]
    pattern = "|".join(ntfs_characters + characters)
    regex = re.compile(pattern, re.UNICODE)
    filename = regex.sub("", s)
    return filename[:max_length].rsplit(" ", 0)[0]


def download_audio_from_youtube(url, dnld_location):
    ydl_opts = {
        "outtmpl": dnld_location,
        "format": "bestaudio[acodec^=mp4a]/mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


if __name__ == "__main__":
    # Read yt metadata from the csv file
    config_parser = ConfigParser()
    config_parser.read("spotify.ini")
    result_csv = config_parser["DEFAULT"]["YtResultsCsvSaveFileName"]
    dnld_folder = config_parser["DEFAULT"]["DownloadFolderPath"]

    with open(result_csv, "r", encoding="utf-8") as result_obj:
        result_csv = csv.reader(result_obj)
        video_ids = []

        for line in result_csv:
            search_title = line[0]
            search_artist = line[1]
            album = line[2]
            cover_art_url = line[3]
            vid_id = line[7]

            # check if we downloaded this before
            if vid_id in video_ids:
                print(f"Duplicate download: {vid_id}")
            else:
                video_ids.append(vid_id)

            # download audio stream
            print(f"Downloading: {search_title} {search_artist} {vid_id}")
            file_name = safe_filename(f"{search_title}_{search_artist}") + ".mp4"
            track_file_path = os.path.join(dnld_folder, file_name)
            track_url = f"https://www.youtube.com/watch?v={vid_id}"
            download_audio_from_youtube(track_url, track_file_path)

            # verify it was downloaded
            if not os.path.exists(track_file_path):
                print("TRACK DID NOT DOWNLOAD!!!!")
                sys.exit(1)

            # download cover art
            cover_image = requests.get(cover_art_url)

            # put tags into track
            metadata = EasyMP4(filename=track_file_path)
            metadata["artist"] = search_artist
            metadata["title"] = search_title
            metadata["album"] = album
            metadata.save()

            # put cover art into track
            metadata = MP4(filename=track_file_path)
            metadata.tags["covr"] = [MP4Cover(cover_image.content)]
            metadata.save()
