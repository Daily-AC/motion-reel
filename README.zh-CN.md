# Motion Reel

**让 agent 用代码导演、作画、配乐并导出动态图形短片的开源 skill。**

[English](README.md) · [Skill 入口](skills/motion-reel/SKILL.md) · [创作方法](skills/motion-reel/references/creative-direction.md) · [制作复盘](skills/motion-reel/references/case-study.md)

[![Codex 成片封面](docs/codex-poster.jpg)](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/codex-showcase.mp4)

[▶ 看15秒 Codex 成片](https://github.com/Daily-AC/motion-reel/releases/download/v0.1.0/codex-showcase.mp4)

这份方法来自一次真实迭代：第一版参数正确，但像会动的排版；第二版运动达标，整体仍显空；最终版保留动作，统一色彩，让光、空间与细节回应主体。一个看似加分的文字倒影，因为不跟随立体字变形，被独立复核指出并删掉了。

## 安装与使用

```sh
npx skills add Daily-AC/motion-reel --skill motion-reel -g
```

也可以克隆仓库，让 agent 直接读取 `skills/motion-reel/SKILL.md`。主体是普通 Markdown、Python 和 Node 脚本，`agents/openai.yaml` 只是可选的 Codex 展示元数据。

试着这样提需求：

> 用 $motion-reel 给虚构的精密相机品牌 EMBER 做15秒宣传片。琥珀、象牙白和近黑，主题是“Find your focus”，有原创器乐配乐，交付能播放的 MP4。

## 沉淀了什么

- 先确定一个视觉命题，再设计镜头怎样把同一个元素交给下一镜。
- 用准备、爆发、过冲和恢复设计运动，避免每镜头都只是缓出入场。
- “空”时检查环境有没有回应主体，选择光池、远层线框、地面和投影；保留文字与落版需要的留白。
- 用实际品牌素材，保住轮廓与负空间，再添加倒角、厚度和转动。
- 用同一张事件表驱动画面和声音；用确定性时间函数逐帧渲染。
- 文案、镜头顺序、每镜时长和声音都放在一个 `project.json` 里：说一句“第二镜慢一点”或“改这个词”，只改一个字段，剪切点、冲击和配乐提示点都会跟着变。
- 用有授权的音乐时，`beats.py` 拿曲子里的底鼓核对节拍网格（只用 librosa 可能锁到反拍或越走越偏）；音乐和登记过来源与授权的音效文件由渲染器按采样点精确放置。
- 讲解短片：从项目真实内容里挑值得做成动画的东西，分镜每一镜标 `path:line` 出处；构建时会拒绝没有引文出处的上屏数字。
- 从最终 MP4 抽帧和15–20fps动作条带，区分文件合格、画面接受和观众反馈；声音另测单声道混合损失和每个剪切点的声画偏差，并给出5个让人戴耳机听的时间点。
- 随机字符串分组可以激发联想，但要选择和删减，不能把随机性当成审美。

包内附有可运行模板、渲染器、原创合成音色、可分发字体、验收脚本和具体失败案例。八镜头、蓝紫色、128BPM是示例，不是所有视频的固定配方。

## 手动跑通

依赖 Node.js 22+、Python 3.10+、FFmpeg/ffprobe、支持 WebGL2 浮点目标的 Chrome/Chromium。浏览器找不到时设置 `CHROME_PATH`。联络表脚本额外用 Pillow，`beats.py` 通过 `uv run --with librosa --with matplotlib` 用 librosa。

```sh
git clone https://github.com/Daily-AC/motion-reel.git
cd motion-reel
python3 skills/motion-reel/scripts/new_project.py ./work/nova --brand NOVA
cd work/nova
node render.mjs doctor
node render.mjs stills 0,0.8,4.6,8.6,10.6,14.3 --samples 8
node render.mjs render --out out/nova.mp4 --samples 16
python3 verify.py out/nova.mp4
```

加 `--scale 2` 出原生4K。`node render.mjs preview` 是无声实时预览。换主题要重写相关的视觉论点与行为；竖版要重新构图。

## 验证与边界

本次实际运行记录见 [validation](docs/validation.md)。macOS/Chrome 已实测；Linux/Windows 有浏览器探测，但未宣称已完成真实渲染验证。其他文字系统需配套字体和版式检查。

这份 skill 能传递方法和工具，不能保证所有模型、主题和审美判断都产出同样结果。声音会测响度、峰值、单声道混合和剪切同步，但测量代替不了听；原作没有进行主观听审。

## 授权与致谢

原创代码与指导采用 [MIT](LICENSE)。字体、图标等保留各自授权，见 [THIRD_PARTY.md](THIRD_PARTY.md)。示例里的 Codex/OpenAI 标志不代表官方背书，也不是提供给其他品牌使用的原创图标。

Daily-AC 与 Claude、Codex 共同制作。底层渲染器来自此前的纯代码视频工作流；这次补齐了创作判断、迭代验收和可迁移工程。用户此前分享的 [Lemo-Opuscar](https://github.com/lemomo-ai/lemo-opuscar) 是相关启发，本包没有搬运其39种风格作品。
