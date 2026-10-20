# py-dlmanager

Docker Compose setup for the React frontend, FastAPI download API, TorBox, and a WebDAV destination.

## Configure

Copy `example.env` to `.env` in the repository root, then replace the placeholder values with your service credentials:

```dotenv
cp example.env .env
```

The WebDAV username and password may be left blank for an anonymous server. The `.env` file is excluded from Git and Docker build contexts.

## Run

From the repository root:

```sh
docker compose up --build -d
```

Open <http://localhost:8080>. The frontend container proxies API requests to the API service. The API is not published directly to the host. Shelf data is stored in the persistent `download_data` named volume.

To stop the services, run `docker compose down`. The named volume is retained; `docker compose down -v` removes it and permanently deletes the saved download queue.

## Publish container images

The Gitea Actions workflow builds and publishes the API and frontend images to the Gitea container registry on branch pushes, version tags (`v*`), or manual runs. Add the repository secret `REGISTRY_TOKEN` with a Gitea token that can publish packages. The workflow derives the registry host from the Gitea Actions server URL (without its scheme), uses the repository path as the package owner/image namespace, and uses the triggering actor as the registry username, so the token must belong to that account.

The runner must be able to reach the registry and a Docker daemon; for a local HTTP registry, configure the daemon to allow that insecure registry.

Both images are published with `latest` and the commit-SHA tag on every run. On a version-tag push such as `v1.2.3`, each image is also published with that version tag, for example `<registry>/<owner>/py-dlmanager-api:v1.2.3` and `<registry>/<owner>/py-dlmanager-frontend:v1.2.3`.