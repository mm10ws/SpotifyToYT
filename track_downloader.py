import os
import sys
import csv
import requests
from configparser import ConfigParser
from pytube import YouTube
from pytube.helpers import safe_filename
from mutagen.easymp4 import EasyMP4
from mutagen.mp4 import MP4, MP4Cover


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
            yt = YouTube(f"https://www.youtube.com/watch?v={vid_id}")

            # TODO: getting a weird keyerror from pytube sometimes, so just keep retrying
            try_again = True
            while try_again:
                try:
                    result = yt.streams.get_audio_only()
                    try_again = False
                except Exception:
                    print("Failed, trying again...")

            file_name = (
                safe_filename(f"{search_title}_{search_artist}") + f".{result.subtype}"
            )
            result.download(output_path=dnld_folder, filename=file_name)

            # verify it was downloaded
            track_file_path = os.path.join(dnld_folder, file_name)
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
            metadata.tags["covr"] = [(MP4Cover(cover_image.content))]
            metadata.save()
