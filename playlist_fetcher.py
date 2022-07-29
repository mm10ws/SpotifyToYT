from datetime import datetime
from spotipy import Spotify
from configparser import ConfigParser
from spotipy.oauth2 import SpotifyClientCredentials

SPOTIFY_DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

if __name__ == "__main__":
    # Read spotify id and secret from config file
    config_parser = ConfigParser()
    config_parser.read("spotify.ini")
    client_id = config_parser["DEFAULT"]["ClientId"]
    client_secret = config_parser["DEFAULT"]["ClientSecret"]
    playlist_link = config_parser["DEFAULT"]["PlaylistLink"]
    csv_save_location = config_parser["DEFAULT"]["PlaylistCsvSaveFileName"]

    # Figure out at what point do we want to take songs since, beginning of time if it is omitted
    if "TracksSince" in config_parser["DEFAULT"]:
        tracks_since = datetime.strptime(
            config_parser["DEFAULT"]["TracksSince"], SPOTIFY_DATETIME_FORMAT_STRING
        )
    else:
        tracks_since = datetime.utcfromtimestamp(0)

    print(
        f"Fetching songs on playlist {playlist_link} since {tracks_since.strftime(SPOTIFY_DATETIME_FORMAT_STRING)}..."
    )

    # Query spotify api and build up a list of tracks
    spotify = Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )
    results = spotify.playlist_items(playlist_id=playlist_link)
    tracks = results["items"]
    while results["next"]:
        results = spotify.next(results)
        tracks.extend(results["items"])

    with open(csv_save_location, "w", encoding="utf-8") as f:
        added_track_count = 0
        for track in tracks:
            add_datetime = datetime.strptime(
                track["added_at"], SPOTIFY_DATETIME_FORMAT_STRING
            )

            # Only include the track if the date it was added is after out cutoff point
            if add_datetime >= tracks_since:
                title = track["track"]["name"].replace(",", " ")
                artist = track["track"]["artists"][0]["name"].replace(",", " ")
                album = track["track"]["album"]["name"].replace(",", " ")
                cover_art = track["track"]["album"]["images"][0]["url"]
                f.write(f"{title},{artist},{album},{cover_art}\n")
                added_track_count += 1

    print(f"Saved {added_track_count} songs to {csv_save_location}")
