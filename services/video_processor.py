"""
Video processor for extracting audio and transcribing video files.
"""
import os
import tempfile
from faster_whisper import WhisperModel
from moviepy import VideoFileClip
from typing import Optional


class VideoProcessor:
    """Process video files and generate transcripts."""

    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv", ".wmv"}
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}

    def __init__(self, whisper_model: str = "base"):
        """
        Initialize video processor.

        Args:
            whisper_model: Whisper model size (tiny, base, small, medium, large)
        """
        self.whisper_model_name = whisper_model
        self._whisper_model = None

    @property
    def whisper_model(self):
        """Lazy load the whisper model."""
        if self._whisper_model is None:
            self._whisper_model = WhisperModel(self.whisper_model_name, compute_type="int8")
        return self._whisper_model

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """Get the file extension from filename."""
        return os.path.splitext(filename)[1].lower()

    @classmethod
    def is_supported(cls, filename: str) -> bool:
        """Check if file type is supported."""
        ext = cls.get_file_extension(filename)
        return ext in cls.SUPPORTED_VIDEO_EXTENSIONS or ext in cls.SUPPORTED_AUDIO_EXTENSIONS

    @classmethod
    def is_video(cls, filename: str) -> bool:
        """Check if file is a video."""
        ext = cls.get_file_extension(filename)
        return ext in cls.SUPPORTED_VIDEO_EXTENSIONS

    @classmethod
    def is_audio(cls, filename: str) -> bool:
        """Check if file is audio."""
        ext = cls.get_file_extension(filename)
        return ext in cls.SUPPORTED_AUDIO_EXTENSIONS

    def extract_audio_from_video(self, video_path: str, output_path: str) -> str:
        """
        Extract audio from video file.

        Args:
            video_path: Path to video file
            output_path: Path for output audio file

        Returns:
            Path to extracted audio file
        """
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(output_path, verbose=False, logger=None)
        video.close()
        return output_path

    def transcribe_audio(self, audio_path: str) -> dict:
        """
        Transcribe audio file using Whisper.

        Args:
            audio_path: Path to audio file

        Returns:
            Transcription result with text and segments
        """
        segments, info = self.whisper_model.transcribe(audio_path)

        segments_list = []
        full_text = []

        for segment in segments:
            segments_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            full_text.append(segment.text)

        return {
            "text": " ".join(full_text),
            "segments": segments_list,
            "language": info.language if info.language else "unknown"
        }

    def process_video(self, filename: str, file_content: bytes) -> dict:
        """
        Process video file: extract audio and transcribe.

        Args:
            filename: Original filename
            file_content: Video file content as bytes

        Returns:
            Dictionary containing transcript and metadata
        """
        ext = self.get_file_extension(filename)

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as video_tmp:
            video_tmp.write(file_content)
            video_path = video_tmp.name

        audio_path = None

        try:
            if self.is_video(filename):
                # Extract audio from video
                audio_path = tempfile.mktemp(suffix=".wav")
                self.extract_audio_from_video(video_path, audio_path)
                transcription = self.transcribe_audio(audio_path)
            else:
                # It's already an audio file
                transcription = self.transcribe_audio(video_path)

            return {
                "transcript": transcription["text"],
                "segments": transcription["segments"],
                "language": transcription["language"],
                "source_filename": filename
            }

        finally:
            # Cleanup temporary files
            if os.path.exists(video_path):
                os.unlink(video_path)
            if audio_path and os.path.exists(audio_path):
                os.unlink(audio_path)

    def get_transcript_only(self, filename: str, file_content: bytes) -> str:
        """
        Get only the transcript text from a video/audio file.

        Args:
            filename: Original filename
            file_content: File content as bytes

        Returns:
            Transcript text
        """
        result = self.process_video(filename, file_content)
        return result["transcript"]
