---
name: video-link-transcript-digest
description: Trigger on “转录 + URL” to turn Xiaohongshu, Douyin, and YouTube links into a cleaned transcript, summary, and Reality Check.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# Video Link Transcript Digest

## Trigger

Use this workflow when the user sends:

- `转录 <url>`
- `转录这个视频 <url>`
- `总结这个视频 <url>`
- or directly asks to digest a Xiaohongshu / Douyin / YouTube video link

## Output Contract

Always produce three sections:

1. `总结`
2. `Reality Check`
3. `转录稿`

Do **not** output legacy sections such as:

- 内容结构与表达风格
- 亮点
- 适合谁看
- 可执行建议

## Critical Processing Order

1. fetch subtitles or audio
2. create the raw transcript
3. clean the transcript first
4. generate Summary + Reality Check from the cleaned transcript
5. show the cleaned transcript to the user

## Implementation

- CLI: `src/tldr_skill/cli.py`
- Core pipeline: `src/tldr_skill/video_digest.py`
- Tests: `tests/test_video_digest.py`
