import os
import subprocess
import sys
import argparse
from pathlib import Path
from typing import List
import whisper
from tqdm import tqdm
import shutil
import torch
from .config import (
    WHISPER_MODEL,
    OUTPUT_DIR,
    TEMP_DIR,
    NETFLIX_SUBTITLE_STYLE,
    VIDEO_FORMAT,
    AUDIO_FORMAT,
    MAX_RETRIES,
    CLEANUP_TEMP_FILES
)

class SubtitlePipeline:
    def __init__(self, output_dir: str = OUTPUT_DIR):
        self.output_dir = Path(output_dir)
        self.temp_dir = Path(TEMP_DIR)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        print(f"Loading Whisper model: {WHISPER_MODEL}...")
        try:
            self.whisper_model = whisper.load_model(WHISPER_MODEL)
        except TypeError as e:
            if "weights_only" in str(e):
                print("Applying compatibility fix for PyTorch/Whisper version conflict...")
                original_torch_load = torch.load
                def patched_torch_load(*args, **kwargs):
                    kwargs.pop('weights_only', None)
                    return original_torch_load(*args, **kwargs)
                
                torch.load = patched_torch_load
                self.whisper_model = whisper.load_model(WHISPER_MODEL)
                torch.load = original_torch_load
            else:
                raise
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        dependencies = {
            "yt-dlp": "yt-dlp --version",
            "ffmpeg": "ffmpeg -version"
        }
        
        missing = []
        for name, cmd in dependencies.items():
            try:
                subprocess.run(cmd.split(), capture_output=True, check=True)
                print(f"✓ {name} is available")
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing.append(name)
                print(f"✗ {name} is not available")
        
        if missing:
            print(f"\nMissing dependencies: {', '.join(missing)}")
            self._show_installation_instructions(missing)
            return False
        return True
    
    def _show_installation_instructions(self, missing):
        """Show installation instructions for missing dependencies"""
        print("\nInstallation Instructions:")
        print("=" * 50)
        
        if "yt-dlp" in missing:
            print("To install yt-dlp:")
            print("   pip install yt-dlp")
            print()
        
        if "ffmpeg" in missing:
            print("To install FFmpeg:")
            print("   Windows: Download from https://ffmpeg.org/download.html")
            print("   macOS: brew install ffmpeg")
            print("   Linux: sudo apt install ffmpeg")
            print("   Then add FFmpeg to your system PATH")
            print()
        
        print("After installing dependencies, run subplz again!")
    
    def download_video(self, url: str, video_id: str) -> tuple[str, str]:
        """Download video and audio separately for better quality"""
        video_path = self.temp_dir / f"{video_id}.mp4"
        audio_path = self.temp_dir / f"{video_id}.wav"
        
        print(f"Downloading video: {url}")
        

        video_cmd = [
            "yt-dlp",
            "-f", VIDEO_FORMAT,
            "-o", str(video_path),
            url
        ]
        

        audio_cmd = [
            "yt-dlp",
            "-f", AUDIO_FORMAT,
            "--extract-audio",
            "--audio-format", "wav",
            "-o", str(audio_path),
            url
        ]
        

        for attempt in range(MAX_RETRIES):
            try:
                subprocess.run(video_cmd, check=True, capture_output=True)
                subprocess.run(audio_cmd, check=True, capture_output=True)
                return str(video_path), str(audio_path)
            except subprocess.CalledProcessError as e:
                if attempt == MAX_RETRIES - 1:
                    print(f"Error downloading {url} after {MAX_RETRIES} attempts: {e}")
                    return None, None
                print(f"Download attempt {attempt + 1} failed, retrying...")
        
        return None, None
    
    def generate_subtitles(self, audio_path: str, video_id: str) -> str:
        """Generate subtitles using Whisper"""
        print(f"Generating subtitles for {video_id}...")
        

        result = self.whisper_model.transcribe(audio_path)
        

        srt_path = self.temp_dir / f"{video_id}.srt"
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(result["segments"]):
                start_time = self.seconds_to_srt_time(segment["start"])
                end_time = self.seconds_to_srt_time(segment["end"])
                text = segment["text"].strip()
                
                f.write(f"{i + 1}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
        
        return str(srt_path)
    
    def seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        milliseconds = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"
    
    def burn_subtitles(self, video_path: str, srt_path: str, video_id: str) -> str:
        """Burn clean white subtitles into video using FFmpeg"""
        output_path = self.output_dir / f"{video_id}_with_subtitles.mp4"
        
        print(f"Burning clean burned-in subtitles into {video_id}...")
        

        srt_path_fixed = srt_path.replace('\\', '/')
        

        subtitle_style = ",".join([
            f"Fontname={NETFLIX_SUBTITLE_STYLE['fontname']}",
            f"Fontsize={NETFLIX_SUBTITLE_STYLE['fontsize']}",
            f"Bold={'1' if NETFLIX_SUBTITLE_STYLE['bold'] else '0'}",
            f"PrimaryColour={NETFLIX_SUBTITLE_STYLE['primary_colour']}",
            f"SecondaryColour={NETFLIX_SUBTITLE_STYLE['secondary_colour']}",
            f"OutlineColour={NETFLIX_SUBTITLE_STYLE['outline_colour']}",
            f"BackColour={NETFLIX_SUBTITLE_STYLE['back_colour']}",
            f"BorderStyle={NETFLIX_SUBTITLE_STYLE['border_style']}",
            f"Outline={NETFLIX_SUBTITLE_STYLE['outline']}",
            f"Shadow={NETFLIX_SUBTITLE_STYLE['shadow']}",
            f"Alignment={NETFLIX_SUBTITLE_STYLE['alignment']}",
            f"MarginL={NETFLIX_SUBTITLE_STYLE['margin_left']}",
            f"MarginR={NETFLIX_SUBTITLE_STYLE['margin_right']}",
            f"MarginV={NETFLIX_SUBTITLE_STYLE['margin_vertical']}"
        ])
        

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"subtitles='{srt_path_fixed}':force_style='{subtitle_style}'",
            "-c:a", "copy",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-y",
            str(output_path)
        ]
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Error burning clean subtitles for {video_id}:")
            print(f"Command: {' '.join(cmd)}")
            print(f"Error output: {e.stderr}")
            

            print("Trying alternative clean subtitle method...")
            return self.burn_subtitles_alternative(video_path, srt_path, video_id)
    
    def burn_subtitles_alternative(self, video_path: str, srt_path: str, video_id: str) -> str:
        """Alternative clean burned-in subtitle method using a different approach"""
        output_path = self.output_dir / f"{video_id}_with_subtitles.mp4"
        

        temp_srt = self.temp_dir / "temp_subtitle.srt"
        shutil.copy2(srt_path, temp_srt)
        

        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", (
                "subtitles=temp/temp_subtitle.srt:"
                "force_style='"
                "Fontname=Arial Bold,Fontsize=24,PrimaryColour=&Hffffff,"
                "OutlineColour=&H000000,BorderStyle=0,"
                "Outline=2,Shadow=1,Alignment=2,MarginV=40'"
            ),
            "-c:a", "copy",
            "-y",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Alternative clean subtitle method also failed: {e}")

            return self.burn_subtitles_basic_fallback(video_path, srt_path, video_id)
    
    def burn_subtitles_basic_fallback(self, video_path: str, srt_path: str, video_id: str) -> str:
        """Basic fallback subtitle burning"""
        output_path = self.output_dir / f"{video_id}_with_subtitles.mp4"
        temp_srt = self.temp_dir / "simple.srt"
        shutil.copy2(srt_path, temp_srt)
        
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", "subtitles=temp/simple.srt",
            "-c:a", "copy",
            "-y",
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(output_path)
        except subprocess.CalledProcessError as e:
            print(f"Even basic fallback failed: {e}")
            return None
    
    def get_video_title(self, url: str) -> str:
        """Get video title for filename"""
        try:
            cmd = ["yt-dlp", "--get-title", url]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            title = result.stdout.strip()

            title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_'))
            title = title.replace(' ', '_')
            title = title[:30]
            return title if title else f"video_{hash(url) % 10000}"
        except:
            return f"video_{hash(url) % 10000}"
    
    def process_video(self, source: str) -> bool:
        """Process a single video (URL or local file)"""
        try:
            if source.startswith(('http://', 'https://')):

                video_id = self.get_video_title(source)
                print(f"\n{'='*60}")
                print(f"Processing YouTube video: {video_id}")
                print(f"URL: {source}")
                print(f"{'='*60}")
                

                video_path, audio_path = self.download_video(source, video_id)
                if not video_path or not audio_path:
                    return False
            else:

                video_path = Path(source)
                if not video_path.exists():
                    print(f"Video file not found: {source}")
                    return False
                
                video_id = video_path.stem
                print(f"\n{'='*60}")
                print(f"Processing local video: {video_id}")
                print(f"Path: {source}")
                print(f"{'='*60}")
                

                audio_path = self.temp_dir / f"{video_id}.wav"
                audio_cmd = [
                    "ffmpeg",
                    "-i", str(video_path),
                    "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                    str(audio_path),
                    "-y"
                ]
                
                try:
                    subprocess.run(audio_cmd, check=True, capture_output=True)
                    video_path = str(video_path)
                    audio_path = str(audio_path)
                except subprocess.CalledProcessError as e:
                    print(f"Error extracting audio from local video: {e}")
                    return False
            

            srt_path = self.generate_subtitles(audio_path, video_id)
            

            final_path = self.burn_subtitles(video_path, srt_path, video_id)
            
            if final_path:
                print(f"Successfully processed: {final_path}")
                

                if CLEANUP_TEMP_FILES:
                    for temp_file in [audio_path, srt_path]:
                        if os.path.exists(temp_file):
                            os.remove(temp_file)

                    if source.startswith(('http://', 'https://')) and os.path.exists(video_path):
                        os.remove(video_path)
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Error processing {source}: {e}")
            return False
    
    def cleanup(self):
        """Clean up temporary files"""
        if CLEANUP_TEMP_FILES and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)


def main():
    """Main CLI entry point"""
    print("SubPlz - Subtitle Pipeline for Everyone")
    print("=" * 50)
    
    parser = argparse.ArgumentParser(
        description="Download YouTube videos or process local videos and burn clean burned-in subtitles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  subplz https://www.youtube.com/watch?v=VIDEO_ID
  subplz /path/to/local/video.mp4
  subplz "C:\\Users\\Name\\Videos\\myvideo.mp4"
        """
    )
    
    parser.add_argument(
        "source",
        help="YouTube URL or path to local video file"
    )
    
    parser.add_argument(
        "-o", "--output",
        default=OUTPUT_DIR,
        help=f"Output directory (default: {OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    

    pipeline = SubtitlePipeline(output_dir=args.output)
    
    try:

        if not pipeline.check_dependencies():
            return 1
        

        success = pipeline.process_video(args.source)
        
        if success:
            print(f"\nSuccess! Check the '{args.output}' folder for your video with subtitles!")
        else:
            print(f"\nFailed to process: {args.source}")
            return 1
            
    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user.")
        pipeline.cleanup()
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        pipeline.cleanup()
        return 1
    finally:
        pipeline.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
