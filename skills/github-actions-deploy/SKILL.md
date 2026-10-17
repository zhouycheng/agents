---
name: github-actions-deploy
description: >-
  Add or improve GitHub Actions workflows that verify, build, publish, and deploy
  containerized applications to Linux Docker Compose servers. Use for a new
  deployment pipeline or a measured build-speed improvement.
---

# GitHub Actions deployment

Use this skill to add a container deployment workflow or improve an existing one. Keep the workflow aligned with the repository's release branches, build commands, image format, and server deployment contract.

## Inspect the repository

- Read applicable `AGENTS.md` files, deployment documentation, Git state, workflows, build and test commands, Dockerfile, `.dockerignore`, Compose configuration, health endpoints, migration behavior, and any existing rollback command.
- Determine the release branch, registry, target environment, and remote deploy command from repository configuration and existing workflows. Do not assume `main` is production. Ask only for target or safety details that cannot be established from the repository.
- Inspect recent GitHub Actions runs when available. Use `gh run list` and `gh run view` as read-only evidence; do not print secret values or full process environments.
- Preserve existing user changes and deployment contracts. Reuse an existing usable container and deployment setup instead of replacing it for consistency.

## Add or improve the workflow

- Run the repository's required checks on pull requests. Pull-request workflows must not publish or deploy, and must not expose deployment credentials to untrusted code.
- Publish only from the repository's trusted release event after verification succeeds. Give the image an immutable commit-based tag, capture its registry digest, and deploy that digest.
- Use minimal GitHub token permissions, a protected GitHub Environment for deployment credentials when configured, and the repository's established deployment protocol. For a Tailscale target, use GitHub OIDC to join the tailnet and SSH to the restricted remote deploy command.
- Keep health checks and the existing rollback path. Check the application health endpoint and important public routes after deployment. Inspect database migrations before enabling automatic rollout; never add a database reset to a deployment workflow.
- Keep secrets in GitHub secrets or environment settings. Do not add or change repository secrets, protection rules, server configuration, or deployment state unless the user explicitly requested that external change.
- If usable containerization or host deployment support is missing, use the existing `tailscale-docker-deploy` skill to establish those prerequisites; keep this skill focused on the GitHub Actions workflow.
- Confirm the deploy command can restore the last-known-good image. If rollback support is missing, report the prerequisite and coordinate its server-side implementation before claiming the pipeline is release-ready.

## Improve build speed

- Compare recent completed runs and job or step durations. Measure the critical path, accounting for parallel jobs; optimize the measured bottleneck and keep the required checks, smoke tests, and rollback.
- When a self-contained build output can be tested and reused unchanged, build it once in verification, transfer it between jobs as a workflow artifact, record its SHA-256, verify that hash before image packaging, and deploy the resulting image digest.
- If a required artifact is missing or upload/download fails, fail the release job; never rebuild a substitute in the publish job.
- When the Docker build is the canonical output or the app build cannot be handed off safely, build the release image once after verification and use BuildKit external cache for repeatable layers. Keep the build context small and preserve dependency-layer reuse.
- Treat GitHub Actions caches as evictable performance storage. Use a cache to carry a critical build output only when artifact storage or transfer has a verified constraint; use an exact commit key, fail on a cache miss, and verify the artifact hash before publishing.
- Inspect Docker's current official build guidance before changing cache backends, cache mounts, build context, or multi-stage layout. Read [Docker build optimization](references/docker-build-optimization.md) and choose only changes supported by the measured bottleneck.
- Do not remove test coverage or health checks to meet a timing target. Use at least three comparable successful release runs before reporting a median or a sustained improvement; label smaller samples as preliminary.

## Validate and report

- Run the repository's required checks, validate workflow YAML, and use `actionlint` when available. Build the image without pushing when local or CI validation can do so safely.
- Confirm pull requests cannot publish or deploy, failed verification blocks release, any transferred build artifact is required and hash-checked before packaging, deployment uses the digest, and post-deploy checks exercise the intended health surface.
- Report the changed workflow, checks actually run, measured timings and sample size, external GitHub settings still needed, and any deployment behavior that could not be verified.

## Reference patterns

- Read [workflow patterns](references/workflow-patterns.md) when choosing between registry-layer caching and verified build-artifact reuse.
- Read [Docker build optimization](references/docker-build-optimization.md) when changing Docker build behavior.
