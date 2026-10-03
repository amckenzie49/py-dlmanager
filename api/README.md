# py-dlmanager

Manages downloads from TorBox to a WebDAV storage location.

## Configuration

Create an untracked `.env` file in the repository root with the service credentials and destination:

```dotenv
TORBOX_API_KEY=your_torbox_api_key
WEBDAV_URL=https://webdav.example.com/remote.php/dav/files/username
WEBDAV_USERNAME=your_webdav_username
WEBDAV_PASSWORD=your_webdav_password
WEBDAV_REMOTE_PATH=/downloads
```

`WEBDAV_USERNAME` and `WEBDAV_PASSWORD` can be omitted for an anonymous WebDAV endpoint. `TORBOX_BASE_URL`, `DEBRID_POLL_INTERVAL_SECONDS`, and `DEBRID_POLL_TIMEOUT_SECONDS` can be set to override their defaults.

## Run

From the repository root, start the API with:

```sh
api/.venv/bin/uvicorn api.main:app --reload
```

Each queued item moves through `pending`, `debridding`, `ready`, `transferring`, and `completed`. Any processing error moves it to `failed`; the status page refreshes automatically while the workflow runs.
