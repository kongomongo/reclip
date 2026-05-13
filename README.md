# this is my modification, which adds the following features:
- add share button so you dont have to download files but can share them immediatly (warning most browsers have arounda 100MB limit)
- show progress and (approximate) filesize while downloading to ReClip
- add a nice favicon
- dark/gold styling, compact
- Paste Button
- show progress downloading to local device
- show filesizes for the different resolutions
- enable #add? url parameter syntax for sharing from other apps/sites

<img width="766" height="442" alt="image" src="https://github.com/user-attachments/assets/03b61012-5ea2-4ac6-a04e-56fc39a6a1de" /><img width="764" height="532" alt="image" src="https://github.com/user-attachments/assets/9ea4b762-ecb0-44ec-a95e-0133a34e4bc2" /><img width="749" height="148" alt="image" src="https://github.com/user-attachments/assets/a7a9e86c-01a5-48f4-bc71-67482e8d4d9c" /><img width="756" height="144" alt="image" src="https://github.com/user-attachments/assets/1d2710ab-e5e6-44ff-9fa7-84b8a4f2932a" />

# ReClip

A self-hosted, open-source video and audio downloader with a clean web UI. Paste links from YouTube, TikTok, Instagram, Twitter/X, and 1000+ other sites — download as MP4 or MP3.

![Python](https://img.shields.io/badge/python-3.8+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

https://github.com/user-attachments/assets/419d3e50-c933-444b-8cab-a9724986ba05

![ReClip MP3 Mode](assets/preview-mp3.png)

## Features

- Download videos from 1000+ supported sites (via [yt-dlp](https://github.com/yt-dlp/yt-dlp))
- MP4 video or MP3 audio extraction
- Quality/resolution picker
- Bulk downloads — paste multiple URLs at once
- Automatic URL deduplication
- Clean, responsive UI — no frameworks, no build step
- Single Python file backend (~150 lines)

## Quick Start

```bash
brew install yt-dlp ffmpeg    # or apt install ffmpeg && pip install yt-dlp
git clone https://github.com/averygan/reclip.git
cd reclip
./reclip.sh
```

Open **http://localhost:8899**.

Or with Docker:

```bash
docker build -t reclip . && docker run -p 8899:8899 reclip
```

## Usage

1. Paste one or more video URLs into the input box
2. Choose **MP4** (video) or **MP3** (audio)
3. Click **Fetch** to load video info and thumbnails
4. Select quality/resolution if available
5. Click **Download** on individual videos, or **Download All**

## Supported Sites

Anything [yt-dlp supports](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md), including:

YouTube, TikTok, Instagram, Twitter/X, Reddit, Facebook, Vimeo, Twitch, Dailymotion, SoundCloud, Loom, Streamable, Pinterest, Tumblr, Threads, LinkedIn, and many more.

## Stack

- **Backend:** Python + Flask (~150 lines)
- **Frontend:** Vanilla HTML/CSS/JS (single file, no build step)
- **Download engine:** [yt-dlp](https://github.com/yt-dlp/yt-dlp) + [ffmpeg](https://ffmpeg.org/)
- **Dependencies:** 2 (Flask, yt-dlp)

## Disclaimer

This tool is intended for personal use only. Please respect copyright laws and the terms of service of the platforms you download from. The developers are not responsible for any misuse of this tool.

## License

[MIT](LICENSE)
