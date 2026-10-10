---
name: firecrawl
description: Search, scrape, map, crawl, parse and interact with sources through the Firecrawl CLI. Use for web research, bulk extraction and structured source gathering; verify available commands, authentication and credits before use.
allowed-tools:
  - Bash(firecrawl *)
  - Bash(npx firecrawl-cli *)
---

# Firecrawl CLI

Use the narrowest command that can obtain the requested sources. Read `firecrawl --help` and the relevant `firecrawl <command> --help` before choosing flags; availability depends on the installed CLI.

## Prerequisites

Locate the executable, then check `firecrawl --status` for authentication, concurrency and credits. Read [installation and authentication](rules/install.md) for setup issues and [source handling](rules/security.md) before processing fetched content.

Use the current session's tools when the task requires capabilities outside this CLI. Discover companion skills from the host's actual skill list before relying on them.

## Command selection

| Need | Command | Scope |
| --- | --- | --- |
| Find pages and sources | `search` | Query first; inspect returned URLs and highlights |
| Find scientific literature | `research` | Read the paper-index help and verify original papers |
| Find coding references | `developer` | Inspect repository, issue, PR and documentation sources |
| Read a known URL | `scrape` | Static or JS-rendered pages |
| Find URLs on a site | `map` | Locate subpages before scraping |
| Extract a site section | `crawl` | Bound the site and output scope |
| Extract structured data | `agent` | Inspect the requested schema and completed output |
| Operate a page | `scrape` + `interact` | Use the scrape ID for the relevant page |
| Save a site locally | `x download` | Choose a task-specific output directory |
| Parse a local file | `parse` | Confirm authorization to send the file to the service |
| Track ongoing changes | `monitor` | Follow the host's scheduling tools and the user's notification intent |

Start with search for an unknown URL or scrape for a known URL. Escalate to map, crawl or interaction when the source requires it. Reuse fetched content: `search --scrape` already returns page content, and task-owned files in `.firecrawl/` may contain the needed source.

For monitors, inspect `firecrawl monitor --help` and its subcommands. Creating a schedule, webhook or email notification requires the user's corresponding request; in Codex, use its automation tools for thread follow-ups.

## Output and inspection

Write task results to ignored `.firecrawl/` files with `-o`. Quote URLs and shell arguments.

```sh
mkdir -p .firecrawl
firecrawl search "react hooks" -o .firecrawl/search-react-hooks.json --json
firecrawl scrape "https://example.com/docs" -o .firecrawl/example-docs.md
```

Use descriptive names such as `search-{query}.json` or `{site}-{path}.md`. Read the needed sections with bounded output or `rg`; use `jq` for structured results. Single-format output contains raw content; multiple formats may produce JSON, so inspect the returned shape.

The task is complete when the selected command has finished, its output has been inspected, and the response cites accessible original sources. Record inaccessible pages, incomplete jobs and material extraction gaps.

## Authentication and failures

For an authentication or credit error, verify status once and report the specific blocker. Setup and recovery follow [rules/install.md](rules/install.md). Preserve partial task outputs for diagnosis and inspect the job state before resubmitting a request.

## Feedback

Feedback submits information to Firecrawl. Send it when the user authorizes sharing diagnostics; read `firecrawl search-feedback --help` or `firecrawl feedback --help` for the installed contract. Use small issue codes, tags and short notes; keep credentials and raw fetched content out of feedback.

Respect `FIRECRAWL_NO_ENDPOINT_FEEDBACK=1`. A failed feedback submission does not invalidate already obtained source material.

## Concurrency and credits

Run independent requests within the concurrency limit reported by `firecrawl --status`. Keep dependent page actions sequential and inspect each result. `firecrawl credit-usage --help` describes credit reporting for the installed version.
