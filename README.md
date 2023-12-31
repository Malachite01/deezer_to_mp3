- [Setup](#setup)
    - [Windows](#windows)
    - [Linux](#linux)
    - [Requirements](#requirements)
- [Usage](#usage)
- [Disclaimer](#disclaimer)

# Setup

To use this project, you will first need to install ffmpeg and ffprobe as they are dependencies of the yt_dlp python package.

**Important**: What you need is ffmpeg binary, NOT the python package of the same name.

### Windows

Install ffmpeg and ffprobe, and add them to your PATH :

https://www.youtube.com/watch?v=7HbfBwehGV4

### Linux

```
sudo apt-get install ffmpeg
```

### Requirements

Then, you will have to install the project dependencies and requirements (no matter wether you are on Windows or Linux).

```
pip install -r requirements.txt
```
# Usage

To use this project and save your playlist, you will first need your playlist number on Deezer. Your playlist number can be obtained via Deezer, on your web browser. In the url at the top of your browser, you can get your playlist number:

![image](https://github.com/Malachite01/deezer_to_mp3/assets/112857106/5ede04cd-fa9c-4e38-80b7-d82f13847c45)

After obtaining your playlist number, simply execute the python script, and paste your playlist number.
The script will then start saving your playlist in a temporary file that will be removed at the end of the download.
After that, a "songs" folder will be created next to the script, in which all of your playlist will be stored as mp3 files.

The progress bar at the bottom is the progress of your whole playlist download, and when a song is downloaded, its name is printed in the console. 

If you launch the script again, after updating your Deezer playlist, it will only download newly added songs.

# Disclaimer

This project is for personal use only, all the songs downloaded via this project are copyrighted. I will not be held accountable for your actions.
