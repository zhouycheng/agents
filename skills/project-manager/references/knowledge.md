# Role knowledge and templates

Use `.agents/role/INDEX.md` under the project root and `.agents/role/<role-id>/ROLE.md`, `MEMORY.md`, and `STATUS.md` for each approved role. Use stable lowercase English IDs with hyphens; the coordinator ID is manager. Initialize only roles required by the approved plan.

These files are explicitly read and maintained project records. Include the read and update requirements in role startup briefs. Use English names, headings, fields, and generated content while preserving existing identifiers, source paths, and quoted evidence accurately. Conversation titles use Simplified Chinese role display names, the required literal AI员工, and full-width separator ｜. Preserve original English profile names separately for attribution.

## Maintenance

- ROLE holds stable responsibilities, the primary Agency Agents profile, project adaptations, and delivery boundaries. Responsibility changes go through the coordinator's approval plan. Record supplementary profiles only when actually used.
- MEMORY holds confirmed, reusable decisions and lessons with dates and evidence. Consolidate duplication and update superseded conclusions. Reference original logs and conversations instead of copying full transcripts.
- STATUS holds the current task summary and is updated at completion, blockage, and handoff. Record timestamps and verification state. Coordinator STATUS also holds the approved plan and next coordination actions.
- INDEX retains assigned conversation numbers, verified IDs, and titles, including historical assignments. Keep intended and confirmed titles distinguishable when naming is pending. Reconcile actual conversation state on recovery using [Role coordination](coordination.md).
- The coordinator owns INDEX; each role owns its files. Before correcting another role's records, ensure that role has stopped writing them.
- Keep records relevant to the project. Store credentials and sensitive personal data in their designated secure storage.

Fill template values with verified facts. Use Pending confirmation for unknown values. For an empty MEMORY file, write "No confirmed reusable lessons yet." Inspect existing content before making targeted updates.

When initializing manager/ROLE.md, state that its responsibilities are planning, role creation/reuse, dispatch, follow-up, and evidence review. Its writable project scope is approved role administration and its own coordination records. Operational implementation, testing, Git delivery, and deployment belong to assigned role conversations. Apply this boundary when reconciling existing coordinator records with the current user-approved role.

## INDEX.md template

```markdown
# Project Role Registry

Project root: <verified absolute path>
Updated: <timestamp with timezone>

| Role ID | Number | Role name | Responsibility | Directory | Conversation ID / host | Conversation title | Conversation state |
| --- | --- | --- | --- | --- | --- | --- | --- |
| manager | 01 | Project Manager | Project planning and role coordination | manager/ | <verified ID or Pending confirmation> | <prefix>01｜AI员工｜项目总管 (Pending confirmation until verified) | <actual state> |
```

## ROLE.md template

```markdown
# <English role name>

Responsibilities: <sustained responsibilities in this project>
Scope: <owned modules and collaboration boundaries>
Delivery standards: <completion criteria>
Collaboration: <input providers and delivery recipients>
Primary Agency Agents profile: <profile name or approved project-specific identity>
Profile source: <verified source path or project-specific rationale>
Project adaptations: <how expertise and practices apply here>
Supplementary profiles: <names, source paths, and specific contributions, or None>

At startup, read MEMORY.md and STATUS.md in this directory and reconcile them with current project facts.
At completion, blockage, or handoff, update STATUS.md. Record confirmed reusable learning in MEMORY.md.
```

## MEMORY.md template

```markdown
# <English role name> Memory

## <Confirmed decision or lesson>

Date: <date>
Conclusion: <current effective conclusion>
Applies when: <scope and limits>
Evidence: <file, commit, or conversation reference>
```

## STATUS.md template

```markdown
# <English role name> Status

Updated: <timestamp with timezone>
Current task: <task and scope>
Execution state: <Pending / In progress / Blocked / Complete>
Completed work and artifacts: <facts and locations>
Verification and evidence: <verified outcomes and pending checks>
Blockers and dependencies: <actual conditions>
Next action: <action and owner>

## Approved plan and authorization

<Coordinator: plan summary, roles, approved creation or reuse and dispatch scope, and confirmation source. Other roles: current task authorization scope.>
```
