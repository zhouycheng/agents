# 文档与媒体能力

以下内容来自 2026 年 9 月 20 日的本机实测。正式交付仍需按项目要求检查内容和实际页面效果。

## 当前入口

- `pdftotext`、`pdftoppm`：PDF 文本提取和页面渲染（poppler 26.09.0）。
- `~/.agents/skills/docling/SKILL.md`：理解 PDF、DOCX 和其他支持的文档内容。
- `~/.agents/skills/pptx/SKILL.md`：处理 PPTX 或 POTX。
- `~/.agents/skills/drawio-skill/SKILL.md`：图表流程绘制。
- `~/.agents/skills/jianying-video-workflow/SKILL.md`：视频制作工作流（framelean 项目自包含 ffmpeg，音频视频处理走项目内工具）。

## 边界

- `pandoc`、`qpdf`、`soffice`、`magick`、`tesseract`、`d2`、`glow`、`officecli` 等文档转换与渲染 CLI 未安装；任务需要时先与用户确认再 `brew install`。
- ffmpeg 按用户决策不装：framelean 项目自包含。
- OCR、语音转写（`tesseract`、`whisper-cli`）暂不可用，需要时再装。

先读取与任务匹配的 Skill 和项目规则，再选择具体入口。工具可执行不代表每种输入格式都能无损处理；涉及版式的文件需要渲染后复核。
