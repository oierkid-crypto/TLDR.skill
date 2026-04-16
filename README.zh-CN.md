# TLDR.skill

<p align="center">
  <a href="README.md"><img alt="English" src="https://img.shields.io/badge/Language-English-111827?style=for-the-badge"></a>
  <a href="README.zh-CN.md"><img alt="简体中文" src="https://img.shields.io/badge/语言-简体中文-2563eb?style=for-the-badge"></a>
</p>

<p align="center"><strong>把小红书、抖音、YouTube 链接，变成更好读的转录稿、总结和 Reality Check。</strong></p>

<p align="center">
  <a href="https://github.com/oierkid-crypto/TLDR.skill"><img alt="Stars" src="https://img.shields.io/github/stars/oierkid-crypto/TLDR.skill?style=social"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/badge/license-MIT-green"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.11%2B-blue">
</p>

---

## 一句话说明

当一个**朋友、老师、同事**从社交媒体甩给你一段**又长、信息密度又高**的视频时，问题往往不是“我能不能打开链接”，而是：

- **我现在根本没时间看完**
- 里面也许有不少有价值的信息，但都埋在长口播里
- 我还是想快速知道：**它讲了什么、重点是什么、哪些地方值得信、哪些地方要谨慎**

**TLDR.skill** 解决的是这条完整价值链：

> **social media 视频链接 -> 获取视频文稿 -> 清理转录稿 -> 总结 -> Reality Check**

核心价值不是单点，而是整条链路打通：

1. 先把小红书 / 抖音 / YouTube 视频**变成文字**
2. 再把原始文稿**清理成可读版本**
3. 然后给你**总结**，快速提炼重点
4. 最后补一个 **Reality Check**，告诉你哪些点更可信、哪些地方要谨慎

所以它不是“更好读一点”而已，而是让视频信息真正变得**可消费、可判断、可分享**。

---

## 它到底做什么？

输入一个来自以下平台的视频链接：

- 小红书 / Xiaohongshu
- 抖音 / Douyin
- YouTube

输出三部分：

1. **总结** —— 这条视频到底在讲什么
2. **Reality Check** —— 哪些点相对可信，哪些地方要谨慎
3. **优化后的转录稿** —— 补标点、修断句、分段，比原始 ASR 更适合阅读

---

## 为什么它和一般摘要工具不一样？

### 普通链路
`视频 -> 原始转录稿 -> 总结`

### TLDR.skill 链路
`视频 -> 原始转录稿 -> 优化后的转录稿 -> 总结 + Reality Check`

这个“先清理转录稿”的步骤非常关键，尤其对这些场景特别有用：

- 中英混杂术语很多
- ASR 容易把 `token / AIDC / Agent` 识别错
- 中文口播没有标点，直接转出来很难读
- 短视频语速快、噪声多、上下文密度高

---

## 最适合哪些场景？

### 1）朋友、老师、同事发来一段又长又密的视频，但你没时间看
这是最典型、也最真实的使用场景：

- 朋友转给你一条创作者视频
- 老师发来一段课程 / 讲座片段
- 同事在群里甩来一个社交媒体链接

这些视频往往：
- 信息密度很高
- 值得看
- 但你当下就是没时间完整看完

这时候你真正需要的不是“稍后再看”，而是立刻拿到：
- 文稿
- 清理后的文稿
- 总结
- Reality Check

### 2）快速做研究
看到有人讲 AI、创业、SaaS、商业模式、流量分发，但不想完整看 10 分钟，只想先知道重点。

### 3）团队里更高质量地转发视频
不是“你去看一下这个视频”，而是直接给同事：
- 总结
- Reality Check
- 转录稿

### 4）把视频沉淀成可搜索的知识资产
把噪声很多的视频链接，转成可以保存、搜索、引用、导出的 Markdown 文档。

---

## 平台处理策略

### YouTube
1. `youtube-transcript-api` 官方 / 现成字幕
2. `yt-dlp` 自动字幕
3. 下载媒体后走 ASR

### 抖音
1. Playwright + 本地 Chrome
2. 捕获真实音轨请求
3. 下载音频
4. 走 STT

### 小红书
1. `yt-dlp` 下载
2. 走 STT

---

## 输出结构示例

```md
# 视频转录 Digest - <标题>

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

## 快速开始

### 1）安装

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -e ".[video]"
```

### 2）运行

```bash
tldr-skill "https://www.youtube.com/watch?v=Mfzucn4f9Xk" --output /tmp/video_digest.md
```

### 3）JSON 输出

```bash
tldr-skill "https://v.douyin.com/xxxx/" --format json
```

---

## 仓库结构

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

现在这个 repo 已经刻意做成 **精简版**，
只保留 TLDR.skill 真正需要的实现，而不是整个 Hermes 快照。

---

## 环境说明

如果目标平台依赖浏览器 cookies：

```bash
export HERMES_YTDLP_COOKIES_FROM_BROWSER=chrome
export HERMES_YTDLP_BROWSER_HOME=/Users/你的用户名
```

如果你要覆盖抖音抓取时的 Chrome 路径：

```bash
export TLDR_SKILL_CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
```

如果你要覆盖 LLM endpoint / model：

```bash
export OPENAI_API_KEY=...
export TLDR_SKILL_MODEL=gpt-4.1-mini
# 可选
export TLDR_SKILL_BASE_URL=...
```

---

## 测试

```bash
pytest -q
```

---

## Hermes 里的触发方式

在 Hermes 中，推荐触发词是：

- `转录 <url>`
- `转录这个视频 <url>`
- `总结这个视频 <url>`

---

## License

MIT。
