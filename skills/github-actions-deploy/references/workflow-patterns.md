# GitHub Actions deployment patterns

Use these patterns to select a build flow for the repository. They describe decisions, not drop-in workflow files; confirm action versions, permissions, cache scopes, and project paths before adapting them.

## Choose the build handoff

| Pattern | Flow | Use when | Main trade-off |
| --- | --- | --- | --- |
| Registry-layer cache | Verify the application, then build and publish the release image with BuildKit cache import/export | The Docker build is the canonical package or its output is not a portable artifact | The release image build still runs after verification; source changes can invalidate application-build layers |
| Verified build artifact | Build and test once, upload that exact output as a workflow artifact, download it for image packaging, and check its SHA-256 | The application produces a self-contained JAR, binary, or static output that the runtime image can consume directly | Artifact transfer and image packaging must preserve the tested output and its runtime files |

## PersonalSpaceWeb pattern

PersonalSpaceWeb verifies code and runs its normal build on pull requests and release pushes. The trusted release workflow then builds and publishes one Docker image with Buildx and a registry-backed cache, records the image digest, and deploys that digest through Tailscale SSH. This is a registry-layer caching pattern.

The container builder runs `npm run build:release`; the verification job runs `npm run build`. They are separate build paths, so do not describe this example as reusing one verified build output. Use it when the Docker image build is the release package and remote layer caching is the useful optimization.

## TourOps pattern

TourOps builds the Spring Boot JAR in the verification job, records its SHA-256, and uses that JAR to build the runtime image. Pull requests validate an image without publishing. The release job restores the same JAR, verifies the hash, publishes one immutable image, and deploys by digest.

TourOps uses a commit-keyed GitHub Actions cache to transfer the JAR because artifact upload hit the repository's storage quota. This is a quota-constrained case, not the default artifact handoff: GitHub describes workflow artifacts as the way to pass files between jobs, while caches can expire or be evicted. If an exact-key cache is used for a release input, fail on a miss and verify its content hash before publishing; never silently rebuild a different artifact in the publish job.

## Shared release safeguards

- Run checks on pull requests and publish or deploy only from the repository's trusted release event.
- Tag images with the source commit, resolve the pushed image to a digest, and use that digest for deployment.
- Keep deployment credentials out of pull-request runs and limit write permissions to the job that publishes.
- Use the server's established deploy command, check the application health endpoint and required routes, and roll back through the existing last-known-good mechanism when a post-deploy check fails.
- Keep database migration behavior separate from development reset procedures. A deployment workflow must not clear application data.
