import sys
import csv
from configparser import ConfigParser
from ytmusicapi import YTMusic

# youtube search context
ytmusic = YTMusic()


def name_match(our_str, their_str):
    is_match = our_str.lower() in their_str.lower()
    return is_match


def find_in_results(search_title, search_artist, result_to_search):
    for single_result in result_to_search:
        # check that our title is a substring of "title" and (case insensistive compare); exclude punctuation, unicode, etc
        if name_match(search_title, single_result["title"]):
            # check that our artist is a substring of any "name" in "artists" (case insensistive compare)
            for artist in single_result["artists"]:
                if name_match(search_artist, artist["name"]):
                    # if first match output "videoId" else keep checking json
                    return (
                        True,
                        single_result["title"],
                        artist["name"],
                        single_result["videoId"],
                    )

    # no match in list then print song and that we cant find it (confirm by hand to see if we can improve our search)
    if len(result_to_search) > 0:
        first_result = result_to_search[0]
        return (
            False,
            first_result["title"],
            first_result["artists"][0]["name"],
            first_result["videoId"],
        )
    else:
        print(f"MISS: title: {search_title} artist: {search_artist}")
        return False, None, None, None


def search_yt(search_title, search_artist):
    # try to find the best result by first searching songs, then videos, then top result
    search_text = f"{search_title} {search_artist}"
    print(f"Searching for: {search_text}")

    # first check for results in songs only
    bulk_result = ytmusic.search(search_text, filter="songs")
    good_result, found_song_title, found_song_artist, found_song_id = find_in_results(
        search_title, search_artist, bulk_result
    )
    if good_result:
        print("Found a good song result")
        return good_result, found_song_title, found_song_artist, found_song_id

    # otherwise check for results in videos only
    bulk_result = ytmusic.search(search_text, filter="videos")
    (
        good_result,
        found_video_title,
        found_video_artist,
        found_video_id,
    ) = find_in_results(search_title, search_artist, bulk_result)
    if good_result:
        print("Found a good video result")
        return good_result, found_video_title, found_video_artist, found_video_id

    # otherwise just return the top result (if its actually a song and not an album or something else)
    accept_types = ["song", "video"]
    general_search = ytmusic.search(search_text)
    for item in general_search:
        if item["category"] == "Top result" and item["resultType"] in accept_types:
            print("Using top result")
            return False, item["title"], item["artists"][0]["name"], item["videoId"]

    # at this point we just use our best song match
    return False, found_song_title, found_song_artist, found_song_id


if __name__ == "__main__":
    # Read spotify tracks from the csv file
    config_parser = ConfigParser()
    config_parser.read("spotify.ini")
    playlist_csv = config_parser["DEFAULT"]["PlaylistCsvSaveFileName"]
    result_csv = config_parser["DEFAULT"]["YtResultsCsvSaveFileName"]

    # open playlist as csv file
    with open(playlist_csv, "r", encoding="utf-8") as pl_obj:
        with open(result_csv, "w", encoding="utf-8") as result_obj:
            pl_csv_file = csv.reader(pl_obj)
            deferred_text_to_write = ""

            # parse csv to get title, artist to search for
            for line in pl_csv_file:
                search_title = line[0]
                search_artist = line[1]
                album = line[2]
                cover_art = line[3]

                good_match, found_title, found_artist, id = search_yt(
                    search_title, search_artist
                )

                # write out what we found to results csv (put good results up top)
                found_title = found_title.replace(",", " ")
                found_artist = found_artist.replace(",", " ")

                if "," in id:
                    print("VIDEO IDS HAVE COMMAS!!!!!")
                    sys.exit(1)

                csv_line_to_write = f"{search_title},{search_artist},{album},{cover_art},{good_match},{found_title},{found_artist},{id}\n"
                if good_match:
                    result_obj.write(csv_line_to_write)
                else:
                    deferred_text_to_write += csv_line_to_write

            # now write all the not great matches that were deferred
            result_obj.write(deferred_text_to_write)
