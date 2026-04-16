# TLDR.skill

**Turn Xiaohongshu, Douyin, and YouTube links into a cleaned transcript, a concise summary, and a Reality Check.**

[中文说明 / Chinese README](README.zh-CN.md)

> TLDR.skill is a public, shareable workflow built on top of the Hermes Agent codebase.
> This repository currently keeps the **full Hermes repo** because the implementation lives inside Hermes-native prototype + skill paths.

---

## What is this?

TLDR.skill is for people who constantly receive video links and want the **usable text version** instead of watching everything end to end.

Give it a video URL from:

- **Xiaohongshu / 小红书**
- **Douyin / 抖音**
- **YouTube**

It produces:

1. **Summary** — the actual takeaway
2. **Reality Check** — what sounds credible vs what needs caution
3. **Cleaned Transcript** — punctuated, paragraphized, easier to read than raw ASR

This is especially useful when you want to:

- digest creator videos quickly
- turn spoken content into notes
- judge whether a video is worth your time
- share key points with teammates
- archive short-form video knowledge in Markdown or PDF

---

## Why this exists

Most video summarizers stop at either:

- raw transcript dumps, or
- fluffy AI summaries

TLDR.skill does one extra thing that matters a lot in practice:

### Processing order

1. Fetch subtitles or audio
2. Generate the **raw transcript**
3. **Repair the transcript first**
   - punctuation
   - sentence boundaries
   - paragraphing
   - obvious ASR term fixes
4. Generate:
   - **Summary**
   - **Reality Check**
5. Export the final digest as Markdown, JSON, and optionally PDF

That order is intentional. Better transcript quality leads to better summaries.

---

## Output format

A typical Markdown output looks like this:

```md
# Video Transcript Digest - <title>

- Platform: <platform>
- URL: <video-url>
- Transcript source: <provider>

## Summary
### One-line takeaway
...

### Key points
- ...

### Signals
- ...

## Reality Check
### Core judgment
...

### What seems credible
- ...

### What needs caution
- ...

### Bottom line
...

## Transcript
...
```

---

## Supported platform strategy

### YouTube
Priority order:
1. official / available captions via `youtube-transcript-api`
2. `yt-dlp` auto subtitles
3. download + ASR fallback

### Douyin
Uses a browser-based fallback instead of relying only on the fragile extractor path:
- Playwright + local Chrome
- capture the real media audio request
- download audio
- run STT

### Xiaohongshu
- download with `yt-dlp`
- run STT

---

## Real usage scenarios

### 1. Founder / operator research
You see a creator video about AI, SaaS, monetization, or distribution and want:
- the real claim
- the evidence quality
- the cleaned transcript for later reference

### 2. Team knowledge capture
Someone drops a Douyin or YouTube link in chat. Instead of “watch this,” you convert it into:
- summary
- reality check
- transcript

### 3. Content monitoring
You want to track recurring narratives across short videos without manually watching all of them.

### 4. Personal note-taking
You prefer reading over watching and want the video turned into searchable text.

---

## Repository layout

The main TLDR.skill implementation currently lives here:

- `prototypes/video_transcript_digest/src/video_digest.py`
- `prototypes/video_transcript_digest/src/cli.py`
- `tests/prototypes/test_video_digest.py`
- `prototypes/video_transcript_digest/README.md`
- `media/video-link-transcript-digest` skill path is represented through Hermes skill usage conventions

This repository contains the broader Hermes Agent framework because TLDR.skill is currently implemented as a Hermes-native workflow rather than a completely standalone package.

---

## Quick start

### 1. Create a virtual environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2. Install the repo with the TLDR dependencies

```bash
pip install -e ".[video-digest]"
```

### 3. Run the digest CLI

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://www.youtube.com/watch?v=Mfzucn4f9Xk" \
  --output /tmp/video_digest.md
```

### 4. JSON output

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://v.douyin.com/xxxx/" \
  --format json
```

---

## Hermes skill trigger

Inside Hermes, this workflow is designed for prompts like:

- `转录 <url>`
- `转录这个视频 <url>`
- `总结这个视频 <url>`

The skill logic is documented in the Hermes skill file for the workflow.

---

## Environment notes

If your Hermes profile runs with an isolated `HOME`, but the target site needs browser cookies, you may need:

```bash
export HERMES_YTDLP_COOKIES_FROM_BROWSER=chrome
export HERMES_YTDLP_BROWSER_HOME=/Users/your-username
```

---

## Tests

```bash
./venv/bin/python -m pytest tests/prototypes/test_video_digest.py -q
```

The prototype has dedicated tests covering:

- platform detection
- transcript cleanup order
- markdown / JSON rendering
- YouTube fallback chain
- Douyin browser fallback
- CLI output

---

## Public repo note

This repo is being published publicly because the workflow is useful beyond a single private workspace.

If you star it, thank you — that helps signal there is real demand for tools that convert noisy video links into structured, readable knowledge.

---

## Attribution

- Base framework: [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- This public repo packages a TLDR-oriented transcript workflow on top of that foundation

---

## License

MIT. See [LICENSE](LICENSE).
