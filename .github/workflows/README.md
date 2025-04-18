https://docs.docker.com/build/ci/github-actions/

and see https://docs.docker.com/build/cache/backends/gha/ for Github Actions cache for docker builds

## Workflows:
1. **BUILD TEST**: [[docker-build-test.yml]](/.github/workflows/docker-build-test.yml)  
     Tests the container building, multi-platform: arm64 and amd64 (_on pull-request to `dev` and `main` branches_)
2. **DEV**: [[docker-build-push-dev.yml]](/.github/workflows/docker-build-push-dev.yml)  
     Builds **and pushes** to DockerHub and GHCR the **`dev`** branch container (_on push_)
3. **PROD**: [[docker-build-push-prod.yml]](/.github/workflows/docker-build-push-prod.yml)  
     Builds **and pushes** to DockerHub and GHCR the **`main`** branch container (_on push_)
