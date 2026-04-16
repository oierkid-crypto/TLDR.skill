from __future__ import annotations

import argparse
from pathlib import Path

from tldr_skill.video_digest import (
    VideoTranscriptDigestError,
    process_video,
    render_json_report,
    render_markdown_report,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tldr-skill")
    parser.add_argument("url", help="Xiaohongshu / Douyin / YouTube video URL")
    parser.add_argument("--output", help="Output file path. If omitted, print to stdout.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")
    parser.add_argument(
        "--language",
        action="append",
        dest="languages",
        help="Preferred YouTube subtitle language. Repeatable, e.g. --language zh --language en",
    )
    parser.add_argument(
        "--skip-youtube-captions",
        action="store_true",
        help="Skip YouTube captions and go straight to media download + ASR",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result = process_video(
            args.url,
            prefer_youtube_captions=not args.skip_youtube_captions,
            languages=args.languages,
        )
    except VideoTranscriptDigestError as exc:
        parser.exit(status=1, message=f"ERROR: {exc}\n")

    output = render_markdown_report(result) if args.format == "markdown" else render_json_report(result)
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
