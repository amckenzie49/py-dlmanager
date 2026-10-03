# py-dlmanager

Docker Compose setup for the React frontend, FastAPI download API, TorBox, and a WebDAV destination.

## Configure

Create a root `.env` file with your service credentials:

```dotenv
TORBOX_API_KEY=your_torbox_api_key
WEBDAV_URL=https://webdav.example.com/remote.php/dav/files/username
WEBDAV_USERNAME=your_webdav_username
WEBDAV_PASSWORD=your_webdav_password
WEBDAV_REMOTE_PATH=/downloads
```

The WebDAV username and password may be omitted for an anonymous server. Optional settings include `TORBOX_BASE_URL`, `DEBRID_POLL_INTERVAL_SECONDS`, `DEBRID_POLL_TIMEOUT_SECONDS`, and `FRONTEND_PORT` (default `8080`). The `.env` file is excluded from Git and Docker build contexts.

## Run

From the repository root:

```sh
docker compose up --build -d
```

Open <http://localhost:8080>. The frontend container proxies API requests to the API service. The API is not published directly to the host. Shelf data is stored in the persistent `download_data` named volume.

To stop the services, run `docker compose down`. The named volume is retained; `docker compose down -v` removes it and permanently deletes the saved download queue.