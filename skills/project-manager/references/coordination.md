# Role coordination

## Select Agency Agents profiles

Group work by sustained responsibilities and inspect roles already registered in INDEX. Before proposing new roles, inspect installed names and descriptions in `~/.codex/agents/`. Parse or search metadata without dumping every full profile into context. Synced TOML profiles typically expose name, description, and developer_instructions.

Prefer an appropriate Agency Agents profile for each responsibility. Select one primary profile per role, then read its full instructions. Preserve its original English profile name for attribution, relevant expertise, working practices, and delivery standards when adapting it to the project. Assign a concise Simplified Chinese display name for conversation titles following the bootstrap naming rules. Add supplementary expertise only when a concrete task requires it, loading only the relevant supplementary profile.

For example, frontend implementation may use Frontend Developer, backend architecture may use Backend Architect, and API verification may use API Tester when those installed profiles match the work. These are examples; choose roles from the actual project needs and available profiles.

Record the primary profile name, source path, project adaptations, and any supplementary profile in ROLE.md. Reuse suitable existing project roles. When no installed profile fits, explain the gap and include a project-specific role in the plan for approval. Profile instructions remain guidance under project rules, available tools, and user authorization. Respect applicable source licenses.

## Route operational requests

For each requested outcome, select or reuse an execution role, define its task and acceptance evidence, obtain any missing plan approval, and dispatch before operational work begins. Keep the coordinator out of the execution assignment.

Examples:
- Commit and push pending changes: reuse the project's Git administrator when suitable. Ask that role to inspect completion evidence, group changes, commit, push only within the user's authorization, and report commit IDs and remote verification.
- Fix an interface: assign the relevant frontend role; request implementation and appropriate validation evidence.
- Run regression checks: assign the testing role; review its results and route failures to the responsible implementer.
- Missing specialist: propose a suitable Agency Agents profile or project-specific role, then create its conversation after approval.

Pass the user's actual action authorization and its limits in the brief. Approval to dispatch does not authorize additional external actions. Existing project roles remain valid even when an exact Agency Agents counterpart is unavailable.

## Allocate conversation titles

Use the naming convention in [Bootstrap and recovery](bootstrap.md). Reserve 01 for the coordinator. Allocate other role conversations sequentially from 02, formatting numbers with at least two digits. Numbers above 99 retain all digits.

Before allocation, inspect INDEX assignments and accessible conversations belonging to the same verified project. Use project membership and verified conversation IDs to identify roles; titles and initials alone cannot establish identity. Different projects can share an initial.

Preserve a reused conversation's existing assignment. For an unassigned conversation, choose the next unused number above the highest registered or observed assignment, with 01 as the minimum baseline. Retain historical assignments and allocate serially through the coordinator. Before initialization approval, hold assignments in conversation context; persist them only after approval.

When duplicates exist, use registry records and conversation evidence to determine the established assignment. Keep that assignment and allocate a fresh number to the conflicting unassigned role within approved reuse scope. If ownership is ambiguous, ask the user before changing assignments or creating more roles. Multiple coordinator conversations claiming 01 require the user to identify the active coordinator before further dispatch.

## Use available conversation tools

Discover tools and read their current parameters and constraints before use. Typical Codex app tools include list_projects, list_threads, read_thread, set_thread_title, create_thread, send_message_to_thread, and wait_threads. Invoke only tools actually available, following their authorization requirements.

- Reuse: verify project, responsibilities, conversation ID, and execution state. A matching title alone is insufficient. Check for conflicts with ongoing work before dispatch. For approved reuse, retain its assigned number and apply the full standard title through set_thread_title with its verified threadId.
- Create: the approved plan must explicitly request the role conversation. Resolve projectId through list_projects, then use create_thread with the startup brief and approved task. Pass the full allocated title in create_thread.title, including the project prefix, number, AI员工 literal, and selected Simplified Chinese role display name. Inherit user model settings. The coordinator owns naming; the role need not rename itself.
- Register: record a confirmed threadId only after successful creation. Mark clientThreadId or operation IDs as Creating until resolved; do not use them as confirmed thread IDs. Record the assigned number and confirmed title alongside the verified conversation ID. Emit any creation directive required by the tool.
- Dispatch: use send_message_to_thread for an existing conversation within the approved scope. A new conversation's initial prompt already dispatches its first task.
- Follow up: creation is asynchronous. Use wait_threads for progress, retaining cursors and batching relevant targets. Use read_thread when detailed inspection is needed. Report meaningful changes and avoid repeatedly loading full histories.

Roles report through their final response and STATUS. The coordinator reads those results. Receiving a coordinator message does not itself authorize sending messages back or contacting other roles.

## Startup and task brief

Fill in verified absolute project and role-directory paths before sending:

> Serve as [English role name] in [project root]. Read applicable project instructions, then ROLE.md, MEMORY.md, and STATUS.md in [project root]/.agents/role/[role-id]/. Use the primary Agency Agents identity and project adaptations recorded in ROLE.md. Task: [goal and concrete scope]. Inputs and evidence: [locations]. Dependencies and edit boundaries: [details]. Deliverables and acceptance criteria: [details]. Authorized scope: [details]. Reconcile records with current facts before working. At completion, blockage, or handoff, update your STATUS.md and record confirmed, reusable learning in MEMORY.md. Write generated role records and task briefs in English while preserving identifiers, source paths, and quoted evidence accurately. Report artifacts, verification evidence, pending checks, and next actions in your final response. Report required responsibility changes to the user before adopting them.

Send only context necessary for the task. Assign one active editor per shared file and serialize overlapping changes. When the user approves worktrees, identify each checkout and the integration owner. Roles update files in their own checkout; the coordinator reconciles knowledge updates during integration.

## Failures and delivery

For failed or unavailable naming tools, report the intended title and actual outcome without claiming a successful rename. Preserve the assignment and record naming as pending until confirmed.

If tools are missing, access is denied, or a conversation is unavailable, report the blocker and provide a copyable task brief. For uncertain creation outcomes, inspect conversations and operation status before retrying to avoid duplicates. Record undispatched tasks as Pending dispatch. Keep execution assigned to the role; do not substitute coordinator execution for failed dispatch.

Review completion reports against acceptance criteria and supplied code, artifacts, or test evidence using bounded read-only inspection. Delegate additional tests, builds, reproduction steps, or detailed implementation audits to an appropriate role. Mark contradictions as Pending verification and arrange investigation or correction within existing authorization. Preserve real blockers and pending checks, update coordinator status, and report to the user.
