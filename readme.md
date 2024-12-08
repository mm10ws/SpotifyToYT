# Spotify to Youtube
A collection of scripts to save spotify playlists and find corresponding track on youtube

# convert mp4 to mp3

```bash
parallel 'ffmpeg -i {} -c:a libmp3lame output/{.}.mp3' ::: *.mp4
```
