"""Video transcript digest prototype."""

from .video_digest import (
    VideoTranscriptDigestError,
    process_video,
    render_markdown_report,
)

__all__ = [
    "VideoTranscriptDigestError",
    "process_video",
    "render_markdown_report",
]
