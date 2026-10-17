# Docker build optimization

Measure workflow runs before changing build behavior. Check which job is on the critical path, whether the builder restores external cache, and which Dockerfile instruction invalidates the expensive layers.

## Review in this order

- Reduce the build context with a repository-appropriate `.dockerignore`; avoid sending generated output, local dependencies, credentials, and unrelated files to the builder.
- Copy lockfiles and dependency manifests before frequently changing source files so dependency-install layers survive source edits.
- Configure BuildKit cache import and export for CI runners that do not retain local builder state. Give concurrent branches separate cache refs or serialize writers to a shared ref.
- Use package-manager cache mounts when an invalidated install layer would otherwise redownload dependencies.
- Use multi-stage builds and a runtime image containing only the files and dependencies required to run the application.
- Build only the CPU platforms required by the deployment hosts; emulation can make compilation-heavy multi-platform builds slower.
- Pass build secrets with BuildKit secret mounts. Do not pass credentials through Docker `ARG`, `ENV`, or copied files.

Do not apply every technique to every project. Confirm the Dockerfile syntax and cache-backend behavior against the current official documentation before editing a workflow.

## Official documentation

- [Optimize cache usage in builds](https://docs.docker.com/build/cache/optimize/) covers layer order, small contexts, cache mounts, and external cache.
- [Cache storage backends](https://docs.docker.com/build/cache/backends/) documents `registry`, `gha`, and other BuildKit cache exporters and importers.
- [Multi-stage builds](https://docs.docker.com/build/building/multi-stage/) explains keeping build dependencies out of the runtime image.
- [Multi-platform builds](https://docs.docker.com/build/building/multi-platform/) explains platform selection and the cost of emulation.
- [GitHub Actions workflow artifacts](https://docs.github.com/en/actions/concepts/workflows-and-actions/workflow-artifacts) distinguishes artifacts used to pass job outputs from caches used to reuse files across runs.
