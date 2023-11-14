import requests
import json
import os
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
YOUTUBE_ENDPOINT = "https://www.youtube.com"

def get_youtube_init_data(url):
    init_data = {}
    api_token = None
    context = None
    try:
        page = requests.get(url)
        yt_init_data = page.text.split("var ytInitialData =")[1].split("</script>")[0].strip()[:-1]

        if "innertubeApiKey" in page.text:
            api_token = page.text.split("innertubeApiKey")[1].split(",")[0].split('"')[2]

        if "INNERTUBE_CONTEXT" in page.text:
            context = json.loads(page.text.split("INNERTUBE_CONTEXT")[1].strip()[2:-2])

        init_data = json.loads(yt_init_data)
        return {"initdata": init_data, "apiToken": api_token, "context": context}
    except Exception as ex:
        print(ex)
        return {"initdata": init_data, "apiToken": api_token, "context": context}

def get_data(keyword, with_playlist=False, limit=0, options=None):
    endpoint = f"{YOUTUBE_ENDPOINT}/results?search_query={keyword}"
    try:
        if options and isinstance(options, list) and len(options) > 0:
            type_option = next((opt["type"] for opt in options if "type" in opt), None)
            if isinstance(type_option, str):
                if type_option.lower() == "video":
                    endpoint += "&sp=EgIQAQ%3D%3D"
                elif type_option.lower() == "channel":
                    endpoint += "&sp=EgIQAg%3D%3D"
                elif type_option.lower() == "playlist":
                    endpoint += "&sp=EgIQAw%3D%3D"
                elif type_option.lower() == "movie":
                    endpoint += "&sp=EgIQBA%3D%3D"

        page = get_youtube_init_data(endpoint)

        section_list_renderer = page["initdata"]["contents"]["twoColumnSearchResultsRenderer"]["primaryContents"]["sectionListRenderer"]

        cont_token = {}
        items = []

        for content in section_list_renderer["contents"]:
            if "continuationItemRenderer" in content:
                cont_token = content["continuationItemRenderer"]["continuationEndpoint"]["continuationCommand"]["token"]
            elif "itemSectionRenderer" in content:
                for item in content["itemSectionRenderer"]["contents"]:
                    if "channelRenderer" in item:
                        channel_renderer = item["channelRenderer"]
                        items.append({
                            "id": channel_renderer["channelId"],
                            "type": "channel",
                            "thumbnail": channel_renderer["thumbnail"],
                            "title": channel_renderer["title"]["simpleText"]
                        })
                    else:
                        video_render = item.get("videoRenderer")
                        playlist_render = item.get("playlistRenderer")

                        if video_render and video_render["videoId"]:
                            items.append(video_render)
                        if with_playlist and playlist_render and playlist_render["playlistId"]:
                            items.append({
                                "id": playlist_render["playlistId"],
                                "type": "playlist",
                                "thumbnail": playlist_render["thumbnails"],
                                "title": playlist_render["title"]["simpleText"],
                                "length": playlist_render["videoCount"],
                                "videos": playlist_render["videos"],
                                "videoCount": playlist_render["videoCount"],
                                "isLive": False
                            })

        api_token = page["apiToken"]
        context = page["context"]
        next_page_context = {"context": context, "continuation": cont_token}
        items_result = items[:limit] if limit != 0 else items

        return {"items": items_result, "nextPage": {"nextPageToken": api_token, "nextPageContext": next_page_context}}
    except Exception as ex:
        print(ex)
        return {"error": str(ex)}

def search_and_get_first_video_url(query):
    data = get_data(query, limit=1)
    if "items" in data and data["items"]:
        first_video_id = data["items"][0].get("videoId", None)
        if first_video_id:
            return f"{YOUTUBE_ENDPOINT}/watch?v={first_video_id}"
    return None

def download_mp3(url):
    if not os.path.exists("songs/"):
        os.makedirs("songs/")

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
    
    # DeezerMP3Backup
    json_playlist = playlist_to_json_file(OUTPUT_FILE, api_url, data)
    
    # YouTube Download
    for item in json_playlist:
        song_name = item["song"]
        video_query_url = search_and_get_first_video_url(song_name)

        if video_query_url:
            download_mp3(video_query_url)
        else:
            print(f'No video IDs found for song: {song_name}')
            
    # Delete playlist.json
    os.remove(OUTPUT_FILE)
    
    return

if __name__ == "__main__":
    main()