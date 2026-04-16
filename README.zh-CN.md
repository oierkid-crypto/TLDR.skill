# TLDR.skill

**把小红书、抖音、YouTube 视频链接，变成更好读的转录稿 + 总结 + Reality Check。**

[English README](README.md)

> TLDR.skill 是一个基于 Hermes Agent 代码库构建的可分享工作流。
> 这个公开仓库目前保留了 **完整 Hermes repo**，因为实现仍然落在 Hermes 原生的 prototype + skill 路径里。

---

## 这是什么？

TLDR.skill 适合这样的场景：

你经常收到各种视频链接，但并不想每条都完整看完；你真正想要的是**可消费的文字结果**。

目前支持：

- **小红书 / Xiaohongshu**
- **抖音 / Douyin**
- **YouTube**

输出三部分：

1. **总结** — 这条视频到底在讲什么
2. **Reality Check** — 哪些内容相对可信，哪些地方要谨慎
3. **优化后的转录稿** — 比原始 ASR 更易读，补了标点、断句和分段

它特别适合：

- 快速消化创作者视频
- 把口播内容转成笔记
- 判断一个视频值不值得花时间看
- 给团队转发“精华版”内容
- 把短视频沉淀成 Markdown / PDF 知识资产

---

## 为什么要做这个？

大多数视频摘要工具只做到两种之一：

- 丢给你一份很难读的原始转录稿
- 或者给你一段比较空泛的 AI 总结

TLDR.skill 多做了一步，而且这一步很关键：

### 处理顺序

1. 先抓字幕或音频
2. 生成**原始转录稿**
3. **先修转录稿，再做总结**
   - 补标点
   - 修断句
   - 分段
   - 修明显 ASR 术语错误
4. 再生成：
   - **总结**
   - **Reality Check**
5. 最终导出 Markdown / JSON，必要时还可以生成 PDF

这个顺序不是装饰，而是为了让后续总结质量更可靠。

---

## 输出长什么样？

典型 Markdown 结构如下：

```md
# 视频转录 Digest - <标题>

- 平台：<platform>
- 链接：<video-url>
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

## 平台处理策略

### YouTube
优先级：
1. `youtube-transcript-api` 官方 / 现成字幕
2. `yt-dlp` 自动字幕
3. 下载视频后做 ASR

### 抖音
不只依赖脆弱的 extractor，而是优先走浏览器回退链路：
- Playwright + 本地 Chrome
- 捕获真实 media-audio 请求
- 下载音轨
- 走语音转录

### 小红书
- `yt-dlp` 下载
- 再走 STT

---

## 适合哪些真实使用场景？

### 1）创业者 / 研究者快速消化视频
看到有人讲 AI、SaaS、流量、商业模式，不想花几分钟到十几分钟完整看完，只想知道：
- 结论是什么
- 哪些判断靠谱
- 哪些地方证据不足

### 2）团队内部分享
有人在群里甩一个抖音 / YouTube 链接，不再只是“你去看一下”，而是直接转成：
- 总结
- Reality Check
- 转录稿

### 3）长期内容监测
你想跟踪某类短视频叙事，比如 AI 创业、流量打法、行业观点，但不想人工一条条刷完。

### 4）个人知识管理
你更喜欢“读”而不是“看”，希望把视频变成可搜索、可引用的文本。

---

## 仓库结构说明

TLDR.skill 当前主要实现路径在这里：

- `prototypes/video_transcript_digest/src/video_digest.py`
- `prototypes/video_transcript_digest/src/cli.py`
- `tests/prototypes/test_video_digest.py`
- `prototypes/video_transcript_digest/README.md`

之所以这个仓库里保留了更大的 Hermes Agent 框架，是因为 TLDR.skill 目前还是一个 **Hermes 原生 workflow / skill**，而不是已经完全拆出来的独立 Python 包。

---

## 快速开始

### 1）创建虚拟环境

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 2）安装 TLDR.skill 相关依赖

```bash
pip install -e ".[video-digest]"
```

### 3）运行 CLI

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://www.youtube.com/watch?v=Mfzucn4f9Xk" \
  --output /tmp/video_digest.md
```

### 4）输出 JSON

```bash
PYTHONPATH=prototypes/video_transcript_digest/src:. python \
  prototypes/video_transcript_digest/src/cli.py \
  "https://v.douyin.com/xxxx/" \
  --format json
```

---

## 在 Hermes 里怎么触发？

这个 workflow 在 Hermes 里设计成以下触发方式：

- `转录 <url>`
- `转录这个视频 <url>`
- `总结这个视频 <url>`

也就是说，用户只要像自然语言一样发出“转录 + url”即可。

---

## 环境说明

如果你的 Hermes profile 使用的是隔离的 `HOME`，但目标站点又依赖浏览器 cookies，可以额外设置：

```bash
export HERMES_YTDLP_COOKIES_FROM_BROWSER=chrome
export HERMES_YTDLP_BROWSER_HOME=/Users/你的用户名
```

---

## 测试

```bash
./venv/bin/python -m pytest tests/prototypes/test_video_digest.py -q
```

当前原型测试覆盖了：

- 平台识别
- 转录稿先优化、再总结的处理顺序
- Markdown / JSON 渲染
- YouTube 回退链路
- 抖音浏览器回退链路
- CLI 输出

---

## 为什么公开这个 repo？

因为这个工作流不是只对一个私有工作区有价值。

只要你也有“我经常看到视频链接，但更想直接拿到结构化文字结果”的需求，这个 repo 就可能对你有用。

如果你愿意点个 Star，那就太好了——这能帮助验证：
**把噪声视频链接转成结构化知识，确实是个真实需求。**

---

## 致谢

- 底层框架：[Hermes Agent](https://github.com/NousResearch/hermes-agent)
- 本公开仓库是在其基础上，封装了一个偏 TL;DR 场景的视频转录工作流

---

## License

MIT，见 [LICENSE](LICENSE)。
