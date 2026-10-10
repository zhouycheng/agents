---
name: firecrawl-cli-installation
description: Locate, install and authenticate the official Firecrawl CLI using the workstation's package and skill maintenance workflow.
---

# Firecrawl CLI setup

## Locate and verify

```sh
command -v firecrawl
firecrawl --help
firecrawl --status
```

Help verifies the installed command surface; status checks authentication and account limits. A task-authorized small source request verifies the service and file output:

```sh
mkdir -p .firecrawl
firecrawl scrape "https://firecrawl.dev" -o .firecrawl/install-check.md
```

Inspect the output before reporting the service as usable.

## Installation and updates

The npm package is `firecrawl-cli`. On this workstation, first inspect the existing package and [workstation package workflow](../../workstation-provision/SKILL.md). Installation and upgrades follow the user's explicit decision and the Brewfile declaration.

```sh
npm install -g firecrawl-cli
```

If an installed command is missing from PATH, inspect the npm global prefix and executable location before reinstalling.

`firecrawl init` and `firecrawl setup` can also install integrations and skills across detected hosts. Inspect their help and intended write scope before use. This repository maintains the self-managed Firecrawl skill in `~/.agents/skills/firecrawl/`; review upstream documentation changes here, then use the repository's [host synchronization workflow](../../README.md#宿主同步).

## Authentication

Use the CLI's supported authentication flow after reading `firecrawl login --help`:

```sh
firecrawl login --browser
```

Credentials stay in the CLI's authentication storage. Account and key entry use the tool's supported secure mechanism.

An unauthorized or insufficient-credit result is terminal for that request. Check `firecrawl --status` once, preserve the diagnostic and report the blocker. Endpoint access without an account depends on the installed version and service; verify actual behavior before relying on it.

## Upstream references

- [CLI source](https://github.com/firecrawl/cli)
- [CLI package](https://www.npmjs.com/package/firecrawl-cli)
- [Official CLI documentation](https://docs.firecrawl.dev/sdks/cli)
