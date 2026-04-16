# TLDR.skill

<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/Language-English-111827?style=for-the-badge"></a>
  <a href="README.zh-CN.md"><img alt="简体中文" src="https://img.shields.io/badge/语言-简体中文-2563eb?style=for-the-badge"></a>
</p>

<p align="center"><strong>Turn Xiaohongshu, Douyin, and YouTube links into a cleaned transcript, a sharp summary, and a Reality Check.</strong></p>

<p align="center">
  <a href="https://github.com/oierkid-crypto/TLDR.skill"><img alt="Stars" src="https://img.shields.io/github/stars/oierkid-crypto/TLDR.skill?style=social"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

---

## TL;DR

Most video tools give you either:

- a messy transcript dump, or
- a fluffy AI summary.

**TLDR.skill** does the useful middle step:

> **clean the transcript first, then summarize it.**

That makes the output much more readable and much more trustworthy.

---

## What it does

Input: a video URL from

- Xiaohongshu / 小红书
- Douyin / 抖音
- YouTube

Output:

1. **Summary** — the distilled takeaway
2. **Reality Check** — what seems credible vs what needs caution
3. **Cleaned Transcript** — punctuated, paragraphized, easier to read than raw ASR

---

## Why this is different

### Traditional pipeline
`video -> raw transcript -> summary`

### TLDR.skill pipeline
`video -> raw transcript -> cleaned transcript -> summary + reality check`

That extra cleanup stage matters a lot in practice, especially for:

- mixed Chinese / English terminology
- ASR mistakes like `token` / `AIDC` / `Agent`
- creator videos with poor punctuation after transcription
- short-form video content that is fast, noisy, and context-heavy

---

## Best use cases

### 1. Research faster
You see a video about AI, startups, monetization, or distribution and want the point without spending 10 minutes watching it.

### 2. Share better inside teams
Instead of sending “watch this,” send:
- summary
- reality check
- transcript

### 3. Build a searchable knowledge base
Turn noisy video links into Markdown you can archive, grep, reuse, and export.

### 4. Read instead of watch
If you prefer text over video, this gives you the useful text version.

---

## Supported platform strategy

### YouTube
1. official / existing captions via `youtube-transcript-api`
2. `yt-dlp` auto subtitles
3. media download + ASR fallback

### Douyin
1. Playwright + local Chrome
2. capture the real audio request
3. download audio
4. run STT

### Xiaohongshu
1. `yt-dlp` download
2. STT

---

## Example output shape

```md
# 视频转录 Digest - <title>

- 平台：<platform>
- 链接：<url>
- 转录来源：<provider>

## 总结
### 一句话结论
...

### 核心要点
- ...

### 关键信号
- ...

## Reality Check
### 核心判断
...

### 哪些点相对可信
- ...

### 哪些点需要谨慎
- ...

### 最终结论
...

## 转录稿
...
```

---

## Quick start

### 1. Install

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[video]"
```

### 2. Run

```bash
tldr-skill "https://www.youtube.com/watch?v=Mfzucn4f9Xk" --output /tmp/video_digest.md
```

### 3. JSON mode

```bash
tldr-skill "https://v.douyin.com/xxxx/" --format json
```

---

## Repo structure

```text
src/tldr_skill/
  cli.py
  llm.py
  transcription.py
  video_digest.py
tests/
  test_video_digest.py
skills/
  video-link-transcript-digest/SKILL.md
```

This repo is now intentionally **lean**.
It contains the actual TLDR.skill implementation, not a full Hermes snapshot.

---

## Environment notes

If a target platform needs browser cookies:

```bash
export HERMES_YTDLP_COOKIES_FROM_BROWSER=chrome
export HERMES_YTDLP_BROWSER_HOME=/Users/your-username
```

If you want to override the browser path for Douyin capture:

```bash
export TLDR_SKILL_CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

If you want to override the LLM endpoint / model:

```bash
export OPENAI_API_KEY=...
export TLDR_SKILL_MODEL=gpt-4.1-mini
# optional
export TLDR_SKILL_BASE_URL=...
```

---

## Test

```bash
pytest -q
```

---

## Hermes trigger phrase

Inside Hermes, the intended trigger is:

- `转录 <url>`
- `转录这个视频 <url>`
- `总结这个视频 <url>`

---

## License

MIT.
