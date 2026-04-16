# TLDR.skill prototype

A Hermes-native prototype that ingests a **Xiaohongshu / Douyin / YouTube** video link and returns:

1. a **cleaned transcript**
2. a structured **Summary**
3. a structured **Reality Check**

This prototype is the implementation behind the TLDR.skill workflow documented at the repo root.

---

## Processing order

The order is intentional and important:

1. fetch subtitles or audio
2. generate the raw transcript
3. **repair the transcript first**
   - punctuation
   - sentence boundaries
   - paragraphing
   - obvious ASR term fixes
4. generate:
   - Summary
   - Reality Check
5. render Markdown / JSON, and optionally PDF

---

## Current platform strategy

- **YouTube**: prefer `youtube-transcript-api`; fall back to `yt-dlp` subtitles; then download + ASR.
- **Douyin**: prefer browser fallback (Playwright + local Chrome) to capture the real audio request, then transcribe.
- **Xiaohongshu**: download with `yt-dlp`, then run STT.
- **Summary / Reality Check**: generated through the repo's existing LLM plumbing.

---

## Install

Recommended inside the repo virtual environment:

```bash
./venv/bin/python -m pip install -e ".[video-digest]"
```

If your Hermes profile uses an isolated `HOME` but target sites need browser cookies:

```bash
export HERMES_YTDLP_COOKIES_FROM_BROWSER=chrome
export HERMES_YTDLP_BROWSER_HOME=/Users/your-username
```

---

## Usage

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. ./venv/bin/python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://www.youtube.com/watch?v=Mfzucn4f9Xk" \
  --output /tmp/video_digest.md
```

JSON output:

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. ./venv/bin/python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://v.douyin.com/xxxx/" \
  --format json
```

---

## Output structure

Markdown output contains three sections:

- `## Summary`
- `## Reality Check`
- `## Transcript`

The transcript shown to the user is the **cleaned version**, not the raw ASR dump.

---

## Tests

```bash
./venv/bin/python -m pytest tests/prototypes/test_video_digest.py -q
```

---

## Known limits

- platform download reliability still depends on upstream site behavior
- if neither local STT nor cloud STT is available, media download alone is not enough
- long videos are still summarized through chunking + merge, which is practical but not yet chapter-aware
