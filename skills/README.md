# Agent 技能

自管技能统一在 `~/.agents/skills/` 维护，覆盖工作站、文档与媒体、浏览器、研究、设计及工程开发。本清单列出当前仓库全部 64 个 `SKILL.md` 入口及其用途，含嵌套的 Claude Code 变体。

[技能清单](#技能清单) · [安装](#安装) · [问题反馈](https://github.com/zhouycheng/agents/issues)

## 技能清单

### 通用

| 技能 | 用途 |
|---|---|
| browser-use | 通过 CDP 直接控制浏览器，做自动化、抓取、测试和截图 |
| chatgpt-imagegen | 用已授权的图像生成后端制作图片与 GIF/WebP 动图 |
| codex-with-chatgpt | 用 ChatGPT 辅助规划和评审 Codex 编码任务 |
| composition-patterns | React 组合模式规范，处理布尔 props 膨胀、组件库设计 |
| cross-critique | 让多个独立方案相互评议，深化有争议的技术决策 |
| docling | 把 PDF、DOCX、PPTX、XLSX 等文档转换成 Markdown |
| drawio-skill | 绘制流程图、架构图、UML、网络拓扑等各类图并导出 |
| firecrawl | 通过 Firecrawl CLI 检索网页、提取内容、下载站点 |
| github-actions-deploy | 添加或提速 GitHub Actions 容器镜像构建、发布与服务器部署流程 |
| grill-me | 对想法、方案或决策做逐题压力测试，输出决策简报 |
| grill-me/claude-code | 对明确提出的方案进行逐题压力测试，核实事实并形成决策简报；只访谈，不执行。 |
| implement-specs | 根据已批准的产品与技术规格实现功能并保持规格同步 |
| lark-wiki | 查询、归档和维护飞书个人知识库中的资料与主题 |
| mcp-builder | 构建 Python 或 TypeScript 的 MCP 服务器 |
| no-negative-echo | 按已确认的目标整理正文、标题、文件名和交付说明，保留必要边界事实 |
| playwright-cli | 用 Playwright 自动化浏览器操作与页面测试 |
| pptx | 创建、读取、编辑 PowerPoint 演示文稿 |
| project-manager | 项目总管：明确计划、分派岗位会话并跟进交付 |
| prompt-optimizer-skill | 把草稿提示词改写成可验收的标准结构提示词 |
| workstation-lookup | 从任何项目快速读取本机环境清单、判断时效并定向核验；配置维护由统一工作站技能负责 |
| work-delivery-log | 共享工作成果记录、历史补录与到期目录归档，供 Codex 与 WorkBuddy 共用 |
| workstation-audit | 只读核对工作站配置、能力与本机清单 |
| workstation-provision | 按明确的配置或安装决定部署工作站组件 |
| android-flutter-env | 核验和准备 Android / Flutter、Gradle Wrapper 环境 |
| macos-shell-env | 部署和排查工作站的受管 zsh 环境 |
| react-best-practices | React/Next.js 性能优化规范（Vercel 工程实践） |
| research | 委派多 Agent 调查复杂问题，并返回精炼结论与证据 |
| skill-doctor | 根据真实对话评估 Agent Skills，并提出具体改进建议 |
| tailscale-docker-deploy | 判断或完成 Docker 容器化，并通过 Tailscale SSH 部署到 Linux Compose 服务器 |
| update-skill | 创建、更新和完善本仓库中的 SKILL.md |

### 前端设计

| 技能 | 用途 |
|---|---|
| brandkit | 生成品牌手册图板、logo 系统与视觉识别方案 |
| design-taste-frontend | 解读需求推断设计方向，产出反模板化的前端界面 |
| frontend-design | 前端视觉设计指引，避免模板化审美 |
| gpt-taste | 高端 UX/UI 与 GSAP 滚动动效工程，强化版式与布局变化 |
| image-to-code | 先生成并分析设计图，再按图实现高还原度网页 |
| image-to-psb | 把图片、插画或 PDF 页还原为分层可编辑的 Photoshop PSB |
| imagegen-frontend-mobile | 生成 iOS/Android App 界面概念图与多屏流程 |
| imagegen-frontend-web | 为落地页每个版块单独生成设计参考图 |
| ip-as-logo | 提出 IP 吉祥物方向并生成极简候选图 |
| minimalist-ui | 极简编辑风界面，暖色单色系与扁平 bento 网格 |

### Dart

| 技能 | 用途 |
|---|---|
| dart-add-unit-test | 用 `package:test` 编写和组织单元测试 |
| dart-build-cli-app | 构建命令行应用，处理入口结构与退出码 |
| dart-collect-coverage | 收集测试覆盖率并生成 LCOV 报告 |
| dart-fix-runtime-errors | 抓取运行时堆栈，定位并修复报错行 |
| dart-generate-test-mocks | 用 mockito 生成外部依赖的 mock 对象 |
| dart-migrate-to-checks-package | 把 `expect` 迁移到 `package:checks` 断言 |
| dart-resolve-package-conflicts | 解决 `pub get` 的包版本冲突 |
| dart-run-static-analysis | 运行 `dart analyze` 和 `dart fix` |
| dart-setup-ffi-assets | 用 Native Assets 打包 C/C++ 动态库 |
| dart-use-doc-examples | 在 Dartdoc 中注入外部代码示例 |
| dart-use-ffigen | 用 ffigen 自动生成 FFI 绑定 |
| dart-use-pattern-matching | 使用 switch 表达式和模式匹配 |
| dart-use-primary-constructors | 使用 Dart 3 主构造函数语法 |
| dart-write-documentation | 撰写 `///` API 文档注释 |

### Flutter

| 技能 | 用途 |
|---|---|
| flutter-add-integration-test | 配置集成测试，把交互流程固化为用例 |
| flutter-add-widget-preview | 给 UI 组件添加交互式预览 |
| flutter-add-widget-test | 编写 Widget 组件级测试 |
| flutter-apply-architecture-best-practices | 按 UI、逻辑、数据三层组织应用 |
| flutter-build-responsive-layout | 用 LayoutBuilder 等做响应式布局 |
| flutter-fix-layout-issues | 修复溢出、无界约束等布局错误 |
| flutter-implement-json-serialization | 编写 `fromJson`/`toJson` 模型类 |
| flutter-setup-declarative-routing | 用 go_router 配置声明式路由 |
| flutter-setup-localization | 初始化 `flutter_localizations` 国际化 |
| flutter-use-http-package | 用 http 包请求 REST API |

## 安装

本目录是统一 agents 仓库的技能模块；Git 根目录为 `~/.agents`，工作站配置和 Codex 全局规则分别位于同级 `workstation/`、`codex/`。

```bash
git clone https://github.com/zhouycheng/agents.git ~/.agents
```

## 宿主同步

在交互式终端运行：

```sh
python3 ~/.agents/skills/scripts/sync.py
```

脚本发现已安装的 TRAE CN、Codex、Claude 和 Gemini 目录，由用户选择同步目标；为缺失技能建立逐项软链接，正确链接保持不动，已有真实目录、文件及其他链接保留并列入忽略清单。同步后在新会话核对宿主的技能列表；可发现性取决于宿主支持的目录和配置。

技能及其引用文档在本仓库维护。各技能中的历史设计、实施和版本记录提供追溯信息；执行入口以当前 `SKILL.md`、实际脚本和宿主工具为准。

## 许可

许可按各技能目录中的 `LICENSE`、`LICENSE.txt` 或注明的上游许可核对。
