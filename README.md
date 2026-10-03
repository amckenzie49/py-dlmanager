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