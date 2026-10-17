# Bootstrap and recovery

## Identify the project and request

Confirm the target from the conversation's project, working directory, repository root, and user-provided location. A temporary projectless conversation directory is not sufficient evidence of the intended project. Use list_projects when needed, and ask the user to choose only when the target remains ambiguous.

Inspect applicable AGENTS.md instructions, project summaries, Git status, and `.agents/role/INDEX.md` without making changes. Read only what supports the current decision. Preserve existing work.

## Name the current conversation

Immediately after initial project identification, apply `{prefix}{number}｜AI员工｜{role name}`. Use the uppercase first letter of the verified project name, or the first character's pinyin initial for a Chinese name. Use X when no project is established or an initial cannot be determined. Use a verified project display name rather than an incidental temporary directory name.

The coordinator uses 01 and the Chinese display name 项目总管. Call set_thread_title with the complete title, omitting threadId to target the current conversation. Explicit skill invocation authorizes this startup rename before execution-plan approval. If the project is unknown, use `X01｜AI员工｜项目总管`; update its prefix once the user establishes the project. An already correct title needs no repeated rename.

Examples: `T01｜AI员工｜项目总管`, `T02｜AI员工｜前端工程师`, `L03｜AI员工｜API测试工程师`. These correspond to project initials T and L; use the actual verified project initial.

If the tool is unavailable or fails, report the intended title and actual outcome, then continue discovery. Claim success only when the tool confirms it. Keep the intended title in conversation context until registry initialization is approved.

Use concise Simplified Chinese role display names for every managed conversation. Keep original English profile names in source attribution. Examples: Product Manager as coordinator -> 项目总管; Frontend Developer -> 前端工程师; Backend Architect -> 后端架构师; API Tester -> API测试工程师. Translate other selected profiles by their actual responsibilities and preserve the chosen display name on reuse.

## Clarify the request

For a bare invocation, ask: "What would you like to accomplish in this project?" Clarify the project at the same time if necessary. Explain capabilities for informational requests. Proceed to planning when requirements are sufficiently clear.

## Establish the coordinator identity

Inspect installed profile names and descriptions in `~/.codex/agents/`. Select Agency Agents Product Manager as the default coordinator foundation and read its full instructions, normally in `product-manager.toml`. Adopt relevant product judgment, prioritization, stakeholder communication, and delivery practices alongside this skill's coordination rules.

Treat the profile as guidance under project instructions and user authorization. If unavailable, report the gap and propose a project-specific coordinator identity in the approval plan. Existing approved coordinator records remain the project-specific agreement; reconcile them with current requirements rather than replacing them wholesale.

## Present a plan for approval

Assign an execution owner to every operational task. Keep the coordinator responsible for planning, dispatch, follow-up, and evidence review. A request such as "commit and push the pending changes" authorizes that requested outcome but still requires the role-dispatch plan under this skill; do not begin the Git workflow yourself. Reuse prior confirmed dispatch authorization when it already covers the request.

Specify goals, deliverables, necessary roles and their primary profiles, existing or new conversations, edit boundaries, dependencies, and acceptance criteria. Explicitly identify the role records to initialize or update and the tasks to dispatch to each conversation.

Include any proposed root AGENTS.md changes, worktrees, or model overrides. Default to the existing workspace and user model settings; serialize edits to the same files.

Wait for approval before directory writes, conversation creation, or dispatch. Read-only investigation may continue. Invocation starts coordination; user approval authorizes the stated execution plan.

## Initialize after approval

Read [Role knowledge](knowledge.md). Create `.agents/role/` records for manager and the roles required by the approved plan. Check destination directories, symlinks, and existing files to keep writes within the intended project. Investigate conflicting content before changing it. Add missing information while preserving existing records.

Record the approved plan, authorization scope, confirmation source, and next actions in `.agents/role/manager/STATUS.md`. Persist the verified title and number assignments held in conversation context, register roles, and begin dispatch. Authorization comes from the actual user conversation; disk records are traceability references. Ask the user when historical authorization cannot be verified.

## Recover existing work

Read INDEX, the coordinator's three files, and STATUS for relevant roles. Read role MEMORY when decisions need explanation. Verify conversation state, workspace facts, and evidence before relying on recorded conclusions.

Resume writes and dispatch within verified authorization. Register existing role records after verifying their purpose. Preserve knowledge when a conversation is inaccessible and report its actual status. Propose replacement conversations through the approval flow. Repeated invocation should reuse verified conversations and records.

During recovery, retain stable numbers and reconcile recorded titles with actual conversation state using the allocation rules in [Role coordination](coordination.md). Resolve duplicate assignments before creating additional roles.
