import requests
import json
import yaml
import os
from tqdm import tqdm
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
from pytube.cli import on_progress
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path
from yt_dlp import YoutubeDL


#region DeezerMP3Backup.py
def fetch_data(api_url):
    response = requests.get(api_url)
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Failed to fetch data from the API : {response.status_code}')
        return

def get_penultimate_next_url(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in reversed(lines[:-1]):
            if "next" in line:
                parts = line.split('"')
                return parts[3]
    return

def simplify_data(data):
    simplified_data = []
    song_nb = 0
    for playlist_item in data["playlist"]:
        for item in playlist_item["data"]:
            simplified_item = {
                "song": item["artist"]["name"] + " - " + item["title"]
            }
            simplified_data.append(simplified_item)
            song_nb += 1
    return [simplified_data, song_nb]

def playlist_to_json_file(OUTPUT_FILE, api_url, data):
    # Fetch the plailyst data as json
    while api_url:
        data["playlist"].append(fetch_data(api_url))
        
        # Write the data to the file
        with open(OUTPUT_FILE, "w") as outfile:
            json.dump(data, outfile, indent=4)
       
        # Get the next URL of the playlist because the Deezer API only returns 25 songs at a time
        if api_url != get_penultimate_next_url(OUTPUT_FILE):
            api_url = get_penultimate_next_url(OUTPUT_FILE)
            print(api_url)
        else:
            api_url = None

    # Simplify the data
    filtered_data, song_nb = simplify_data(data)
    
    # Write the data to the file
    with open(OUTPUT_FILE, "w") as outfile:
        json.dump(filtered_data, outfile, indent=4)
    
    print(f"Data simplified, {song_nb} songs found.")
    return filtered_data
#endregion

#region YoutubeAPI.py
def get_creds():
    with open("credentials.yaml", "r") as file:
        creds = yaml.safe_load(file)
    api_key = creds["api_key"]
    return api_key

def get_video_listings(api_key, query):
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)

        search_response = youtube.search().list(
            part='snippet',
            type='video',
            q=query,
            maxResults=1
        ).execute()

        print(yaml.dump(search_response["items"]))
        video_ids = list(
            map(lambda x: x["id"]["videoId"], search_response["items"])
        )
        return video_ids

    except HttpError as e:
        print(f'An HTTP error {e.resp.status} occurred: {e.content}')
        return []

def form_youtube_url(video_id):
    return "http://youtu.be/" + video_id

def download_mp3(video_id):
    if not os.path.exists("songs/"):
        os.makedirs("songs/")
    url = form_youtube_url(video_id)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'songs/%(title)s.%(ext)s',
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        ydl.download([url])

        if 'title' in info_dict:
            print(f'{info_dict["title"]} has been successfully downloaded as an MP3.')
        else:
            print('ERROR: Failed to download the video as an MP3.')
        
#endregion

def main():
    OUTPUT_FILE = "playlist.json"
    api_url = "https://api.deezer.com/playlist/2263829342/tracks"
    data = {"playlist": []}
    
    #DeezerMP3Backup
    json_playlist = playlist_to_json_file(OUTPUT_FILE, api_url, data)
    
    # YouTube API
    api_key = get_creds()
    for item in json_playlist:
        song_name = item["song"]
        video_ids = get_video_listings(api_key, song_name)

        if video_ids:
            for video_id in tqdm(video_ids):
                download_mp3(video_id)
        else:
            print(f'No video IDs found for song: {song_name}')
    return

if __name__ == "__main__":
    main()