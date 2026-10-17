# 工作成果归档

Codex 与 WorkBuddy 共用一个 Skill、统一文案生成程序和 SQLite 账本。保留最近七个自然日，补齐工作记录后，将过期日期目录移入历史归档。两边的“工作成果归档”入口保持暂停，用户按需点击运行。

## 安装

需要 Python 3.9+ 和官方滴答清单 MCP 的读写权限。复制 [配置示例](config.example.json) 到 `~/.config/work-delivery-log/config.json`，填写归档根目录、四位日期所属年份、目标清单名称和 ID。`retention_days` 默认 7，包含当天；`history_root` 默认根目录下的“历史归档”，须为同盘真实目录。配置和状态保存在仓库外。

用仓库的 [技能同步流程](../README.md#宿主同步) 安装到 Codex。WorkBuddy 可使用已有 `~/.workbuddy/skills/` 本地技能目录或官方技能导入入口；导入副本的任务也必须从仓库读取最新 [SKILL.md](SKILL.md)。任务提示词使用 [task-prompt.md](task-prompt.md)，工作目录选 `~/.agents`。创建任务时设置暂停，保存后再次检查开关。

Codex 的官方 MCP 配置入口：

```sh
codex mcp add dida365 --url https://mcp.dida365.com
```

按提示完成 OAuth。WorkBuddy 在连接器中配置同一官方服务，各自保存授权。连接后新会话须实际核对所需工具与清单；配置存在不代表当前会话可调用。

## 使用与状态

```sh
python3 ~/.agents/skills/work-delivery-log/scripts/delivery.py status
python3 ~/.agents/skills/work-delivery-log/scripts/delivery.py preflight --host codex
python3 ~/.agents/skills/work-delivery-log/scripts/delivery.py batch --token TOKEN
python3 ~/.agents/skills/work-delivery-log/scripts/delivery.py archive --token TOKEN
python3 ~/.agents/skills/work-delivery-log/scripts/delivery.py release --token TOKEN
```

主流程见 [SKILL.md](SKILL.md)。`preflight` 先做本地检查与到期整理；空队列自动释放租约，返回 `idle=true`，有待处理成果时才连接滴答清单。`progress` 返回累计待处理、已核验、已归档和本次已知异常；`next_action` 提供条目的续办操作。完成状态通过 `verify` 校验，明确未完成时最多续办原任务三次，失败留待下次手动运行。首次升级自动把已有 `baseline` 转为 `pending`，保留完成记录、任务 ID 和日期映射；首次安装处理全部已有日期成果。每批最多十条，连续获取下一批直至处理完毕；异常条目可用 `batch --exclude ID` 暂时排除，下次续办。运行事件保存在 SQLite 的 `events` 表。

| 状态 | 含义及恢复 |
| --- | --- |
| baseline | 旧版本的历史登记，升级后自动补录 |
| pending | 等待分析和写入 |
| creating | 创建意图已保存，结果不明时先核对同步标识 |
| created | 远端 ID 已保存，续办完成操作 |
| updating | 继续更新相同远端 ID |
| done | 远端完成状态和文案已读回核验 |

活动日期目录先比较浅层元数据，变化的目录再计算内容哈希，AI 仅读取待处理成果；全部完成后在移动前做一次内容检查。历史归档区不扫描文件内容。成果目录只观察一层，深层文件变化可能无法察觉；需要更新记录时重新归档或打包。改名会产生新的路径标识；移除文件不会删除滴答清单任务。

压缩包和成果目录仅在名称明确标注类型时记录为发明或实用新型专利，其他专利成果保留“类别待确认”；研发证明材料按交付用途记录。类型校验在共享程序中执行，两边均使用校验后的标题和详情。

例如 2026-10-11 运行时，保留 10-05 至 10-11，10-04 及以前的完成目录移至 `历史归档/2026/10月/原目录名`。同名历史目录已存在时创建独立批次。需要修改时，将修订成果放回处理区的相同日期和路径，更新原任务后再次归档，旧版本保留。

成果 `source` 保留原路径用于身份和滴答详情；`storage_path` 记录实际保存位置。`moves` 表保存目录来源、目标、文件清单与 `prepared/done/cancelled` 进度。移动意图先提交到账本，再同盘重命名，最后确认实际位置；中断后通过目录身份恢复。来源与目标同时存在或同时缺失时报告异常，保留现状。

年份调整只影响新观察的四位日期目录。跨年推荐新建 `YYYY-MM-DD` 日期目录，保留旧目录及映射；避免在同一根目录重复使用同名 `MMDD` 表示另一年。更换根目录或目标清单时使用独立状态目录（`--state`），保留旧账本。

共享租约和写入意图防止两个执行器同时创建同一成果。远端接口与本地账本之间无法实现原子提交；创建结果不明且查不到任务时保留 `creating` 并报告，避免盲目重试。已有的其他任务不会仅凭相似标题被自动更新。

## 验收

```sh
python3 -m unittest discover -s skills/work-delivery-log/scripts -p 'test_*.py'
git diff --check
```

样例覆盖空运行跳过内容读取与释放租约、完成重试上限和跨宿主续办、旧账本升级、历史补录、七天边界与跨年、一层成果计数、同路径更新、不同日期分开、租约冲突与过期、创建不明及完成失败恢复、远端响应校验、写入期间变更、补充去重、目录冲突与移动中断恢复，并验证历史归档区没有内容读取。两边的模型描述按相同事实标准验收，措辞无需完全一致。

真实联调应选择少量明确的归档成果，核对目标清单、内容与已完成状态，并再次确认两个任务仍暂停。授权记录、账本、工作内容和临时 JSON 留在状态目录；WorkBuddy 可能在工作目录生成 `.workbuddy/` 运行记忆，仓库忽略该目录。Git 管理源代码、说明、示例和测试。

官方依据：[Codex 定时任务](https://learn.chatgpt.com/docs/automations?surface=app)、[WorkBuddy 自动化](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Automation-Guide)、[WorkBuddy 技能](https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market)、[滴答清单 MCP](https://help.dida365.com/articles/7438132116019216384)。

## 月份分类与月度交付包

历史目录统一按年份、月份、日期分层。旧目录位置、月度 ZIP 的安全导入、逐项补录、原始打包保留及中断续办见 [共享操作规则](SKILL.md#月份分类与月度交付包)。
