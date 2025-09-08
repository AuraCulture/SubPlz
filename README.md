# SubPlz 

<img width="200" height="200" alt="subplz_logo" src="https://github.com/user-attachments/assets/1403830e-b3ac-4d8a-9177-5e0c415bd885" />

[![PyPI version](https://badge.fury.io/py/subtitle-for-everyone.svg)](https://pypi.org/project/subtitle-for-everyone/)
[![Python Version](https://img.shields.io/pypi/pyversions/subtitle-for-everyone.svg)](https://pypi.org/project/subtitle-for-everyone/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


**Automatically download YouTube videos and burn clean, professional subtitles into them using AI.**


## Quick Start

Install SubPlz:

Works for latest python version 3.12 (Not recommended)
```bash
pip install ffmpeg (or) https://www.ffmpeg.org/download.html (Recommended and Move bin folder to path)
pip install torch==2.5.1 torchaudio==2.5.1 torchvision==0.20.1
pip install openai-whisper==20231117
pip install subtitle-for-everyone --no-deps
```

Works for python 3.9 > 3.11 (Recommended)
```bash
pip install ffmpeg (or) https://www.ffmpeg.org/download.html (Recommended and Move bin folder to path)
pip install torch
pip install openai-whisper
pip install subtitle-for-everyone
```


Process any YouTube video:
```bash
subplz https://www.youtube.com/watch?v=VIDEO_ID
```

Process local videos:
```bash
subplz /path/to/video.mp4
```

## Features

- **One-command processing** - Just provide a YouTube URL or local video file
- **AI-powered transcription** - Uses OpenAI Whisper for accurate subtitle generation
- **Clean burned-in subtitles** - Professional white text with black outline, no background
- **Automatic cleanup** - Removes temporary files after processing
- **Smart dependency handling** - Guides you through missing dependency installation

## Requirements

- Python 3.8+
- FFmpeg (for video processing)

## How It Works

![SubPlz Demo](https://i.ibb.co/xSwtCS8S/SubPlz.png)

1. **Download** - Fetches video from YouTube or uses your local file
2. **Transcribe** - Uses OpenAI Whisper AI to generate accurate subtitles
3. **Burn** - Embeds clean, professional subtitles directly into the video
4. **Save** - Outputs processed video with `_with_subtitles` suffix

## Output Quality

SubPlz creates professional-grade subtitles:
- White text with black outline for maximum visibility
- Arial Bold font at optimal size
- Bottom center positioning with proper margins
- Perfect readability on any background

## Installation Requirements

### FFmpeg Installation
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

All Python dependencies are installed automatically.

## Advanced Usage

Custom output directory:
```bash
subplz VIDEO_URL -o custom_folder
```

Batch processing:
```python
import subprocess

videos = ["URL1", "URL2", "URL3"]
for url in videos:
    subprocess.run(["subplz", url])
```

## License

MIT License





Made by 🪙


