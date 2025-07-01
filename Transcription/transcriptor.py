from urllib.parse import urlparse
from youtube_transcript_api import YouTubeTranscriptApi
import re
import os
import aiohttp
from moviepy.editor import VideoFileClip
import whisper
import logging

logger = logging.getLogger(__name__)



def detect_platform(link:str) -> str:
   domain = urlparse(link).netloc.lower()
   if "youtube.com" in domain:
        if "shorts" in link:
            return "youtube-shorts"
        else:
            return "youtube"
   elif "tiktok" in domain:
       return "tiktok"
   elif "twitch" in domain:
       return "twitch"
   else:
        return "unknown"
   
def vid_id(url: str) -> str | None:
    match = re.search(r"v=([a-zA-Z0-9_-]{11})", url) or re.search(r"youtu\.be/([a-zA-Z0-9_-]{11})", url)
    return match.group(1) if match else None
   

class AnalyzeMediaLink:
    def __init__(
            self,

    ):
     pass
    
    async def transcript(self, link: str) -> str:
        domain = detect_platform(link=link)
        logger.info(f"Processing link: {link} (platform: {domain})")

        if domain == "youtube":
            transcript = await self.youtube_transcript(link)
        elif domain == "tiktok":
            transcript = await self.tiktok_transcript(link)
        elif domain == "twitch":
            transcript = await self.twitch_transcript(link)
        elif domain == "youtube-shorts":
            transcript = await self.youtube_shorts_transcript(link)
        else:
            transcript = ""
        print(domain)

        return transcript or "No transcript available"
    
    async def youtube_transcript(self, link: str) -> str:
        video_id = vid_id(link)
        if not video_id:
            return "Invalid YouTube URL"
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in transcript])
        except Exception as e:
            return f"Error fetching YouTube transcript: {str(e)}"
        
    async def tiktok_transcript(self, link: str) -> str:
        return await self._download_and_extract_audio(link, "tiktok")

    async def twitch_transcript(self, link: str) -> str:
        return await self._download_and_extract_audio(link, "twitch")

    async def youtube_shorts_transcript(self, link: str) -> str:
        video_id = vid_id(link)
        if not video_id:
            return "Invalid YouTube Shorts URL"
        try:
            # Try YouTubeTranscriptApi first (some Shorts have captions)
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry["text"] for entry in transcript])
        except Exception:
            # Fallback to Whisper if no captions available
            return await self._download_and_extract_audio(link, "youtube-shorts")
    
    async def _download_and_extract_audio(self, link: str, platform: str) -> str:
        """Helper method to download video and extract audio for transcription."""
        temp_video_path = f"temp_{platform}_video.mp4"
        temp_audio_path = f"temp_{platform}_audio.wav"

        try:
            # Download video (using TikMate for TikTok, placeholder for others)
            if platform == "tiktok":
                async with aiohttp.ClientSession() as session:
                    api_url = f"https://tikmate.online/api/?url={link}"
                    async with session.get(api_url) as response:
                        if response.status != 200:
                            return f"Failed to download {platform} video: HTTP {response.status}"
                        data = await response.json()
                        video_url = data.get("url")
                        if not video_url:
                            return f"No video URL found for {platform}"
                        async with session.get(video_url) as video_response:
                            if video_response.status == 200:
                                with open(temp_video_path, "wb") as f:
                                    f.write(await video_response.read())
                            else:
                                return f"Failed to download {platform} video: HTTP {video_response.status}"
            else:
                # Placeholder for Twitch/YouTube Shorts (replace with actual download logic)
                return f"{platform.capitalize()} video download not implemented"

            # Extract audio
            logger.info(f"Extracting audio from {temp_video_path}")
            video = VideoFileClip(temp_video_path)
            video.audio.write_audiofile(temp_audio_path)
            video.close()
            logger.info(f"Extracted audio to {temp_audio_path}")

            # Transcribe with Whisper
            logger.info(f"Transcribing audio with Whisper for {platform}")
            result = self.whisper_model.transcribe(temp_audio_path, language="en")
            transcript = result["text"].strip()
            if not transcript:
                return f"No speech detected in {platform} video"
            return transcript

        except Exception as e:
            logger.error(f"Error processing {platform} transcript: {str(e)}")
            return f"Error processing {platform} transcript: {str(e)}"
        finally:
            # Clean up temporary files
            for path in (temp_video_path, temp_audio_path):
                if os.path.exists(path):
                    try:
                        os.remove(path)
                        logger.info(f"Removed temporary file: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to remove {path}: {str(e)}")


    