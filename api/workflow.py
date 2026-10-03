import asyncio
import time
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any, Callable, Optional
from urllib.parse import quote, urlsplit

import httpx

from api.config import settings
from api.models import Download
from api.storage import storage


class WorkflowError(RuntimeError):
    pass


class TorBoxClient:
    def __init__(self, client: httpx.AsyncClient, api_key: str, base_url: str):
        if not api_key:
            raise WorkflowError("TORBOX_API_KEY is not configured.")
        self.client = client
        self.api_key = api_key
        self.base_url = f"{base_url.rstrip('/')}/v1/api"
        self.headers = {"Authorization": f"Bearer {api_key}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = await self.client.request(
                method,
                f"{self.base_url}/{path.lstrip('/')}",
                headers=self.headers,
                timeout=30,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise WorkflowError(f"TorBox request failed ({type(exc).__name__}).") from None

        try:
            payload = response.json()
        except ValueError:
            payload = {}
        if not response.is_success:
            detail = payload.get("detail") or payload.get("error") if isinstance(payload, dict) else None
            message = f"TorBox request failed (HTTP {response.status_code})."
            if detail:
                message = f"{message} {detail}"
            raise WorkflowError(message)
        if not isinstance(payload, dict):
            raise WorkflowError("TorBox returned an invalid response.")
        if payload.get("success") is False:
            detail = payload.get("detail") or payload.get("error")
            raise WorkflowError(detail or "TorBox rejected the download request.")
        return payload

    async def submit(self, download: Download) -> tuple[str, str]:
        if download.url:
            result = await self._request(
                "POST",
                "webdl/createwebdownload",
                files={"link": (None, download.url)},
            )
            item = result.get("data") or {}
            provider_id = item.get("webdownload_id")
            provider_type = "webdl"
        else:
            magnet = download.magnet_link
            if not magnet and download.info_hash:
                magnet = f"magnet:?xt=urn:btih:{download.info_hash.strip()}"
            if not magnet:
                raise WorkflowError("A direct URL, magnet link, or info hash is required.")
            result = await self._request(
                "POST",
                "torrents/createtorrent",
                files={"magnet": (None, magnet)},
            )
            item = result.get("data") or {}
            provider_id = item.get("torrent_id")
            provider_type = "torrent"

        if provider_id is None:
            raise WorkflowError("TorBox did not return a download ID.")
        return provider_type, str(provider_id)

    async def get_item(self, provider_type: str, provider_id: str) -> Optional[dict[str, Any]]:
        endpoint = "torrents" if provider_type == "torrent" else "webdl"
        result = await self._request(
            "GET",
            f"{endpoint}/mylist",
            params={"id": provider_id, "bypass_cache": "true"},
        )
        data = result.get("data")
        if isinstance(data, list):
            return data[0] if data else None
        return data if isinstance(data, dict) else None

    async def wait_until_ready(
        self,
        provider_type: str,
        provider_id: str,
        poll_interval: float,
        timeout: float,
        on_progress: Optional[Callable[[float], None]] = None,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            item = await self.get_item(provider_type, provider_id)
            if item is not None:
                if item.get("error"):
                    raise WorkflowError(str(item["error"]))
                if on_progress and item.get("progress") is not None:
                    progress = float(item["progress"])
                    on_progress(progress * 100 if 0 <= progress <= 1 else progress)
                if item.get("download_finished") is True:
                    return item
            await asyncio.sleep(poll_interval)
        raise WorkflowError("Timed out waiting for TorBox to finish the download.")

    async def get_download_url(
        self, provider_type: str, provider_id: str, file_id: int
    ) -> str:
        endpoint = "torrents" if provider_type == "torrent" else "webdl"
        id_field = "torrent_id" if provider_type == "torrent" else "web_id"
        result = await self._request(
            "GET",
            f"{endpoint}/requestdl",
            params={
                "token": self.api_key,
                id_field: provider_id,
                "file_id": file_id,
                "redirect": "false",
            },
        )
        link = result.get("data")
        if isinstance(link, dict):
            link = link.get("url") or link.get("link")
        if not isinstance(link, str) or not link.startswith(("http://", "https://")):
            raise WorkflowError("TorBox did not return a valid file URL.")
        return link


class WebDAVClient:
    def __init__(
        self,
        client: httpx.AsyncClient,
        base_url: Optional[str],
        username: Optional[str],
        password: Optional[str],
        remote_path: str,
    ):
        if not base_url:
            raise WorkflowError("WEBDAV_URL is not configured.")
        parsed_url = urlsplit(base_url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise WorkflowError("WEBDAV_URL must be an HTTP or HTTPS URL.")
        if parsed_url.query or parsed_url.fragment:
            raise WorkflowError("WEBDAV_URL cannot include a query or fragment.")
        self.client = client
        self.base_url = base_url.rstrip("/")
        self.auth = httpx.BasicAuth(username, password or "") if username else None
        self.remote_parts = self._safe_parts(remote_path)
        self.remote_path = "/" + "/".join(self.remote_parts)

    @staticmethod
    def _safe_parts(path: str) -> tuple[str, ...]:
        parsed = PurePosixPath(path.replace("\\", "/"))
        if ".." in parsed.parts:
            raise WorkflowError("WebDAV paths cannot contain parent-directory segments.")
        return tuple(part for part in parsed.parts if part not in {"", ".", "/"})

    def _url(self, parts: tuple[str, ...], trailing_slash: bool = False) -> str:
        path = quote("/".join(parts), safe="/")
        suffix = f"/{path}" if path else ""
        if trailing_slash:
            suffix += "/"
        return f"{self.base_url}{suffix}"

    async def _make_collection(self, parts: tuple[str, ...]) -> None:
        response = await self.client.request(
            "MKCOL", self._url(parts, trailing_slash=True), auth=self.auth, timeout=30
        )
        if response.status_code not in {200, 201, 405}:
            raise WorkflowError(
                f"WebDAV directory creation failed (HTTP {response.status_code})."
            )

    async def upload(self, source_url: str, file_name: str) -> tuple[str, str]:
        file_parts = self._safe_parts(file_name)
        if not file_parts:
            raise WorkflowError("TorBox returned an empty file name.")
        target_parts = (*self.remote_parts, *file_parts)
        for index in range(1, len(target_parts)):
            await self._make_collection(target_parts[:index])

        destination_url = self._url(target_parts)
        try:
            async with self.client.stream(
                "GET", source_url, follow_redirects=True, timeout=httpx.Timeout(60, read=None)
            ) as source_response:
                if not source_response.is_success:
                    raise WorkflowError(
                        f"TorBox file download failed (HTTP {source_response.status_code})."
                    )
                response = await self.client.put(
                    destination_url,
                    content=source_response.aiter_bytes(),
                    auth=self.auth,
                    timeout=httpx.Timeout(60, read=None),
                )
        except httpx.RequestError as exc:
            raise WorkflowError(f"File transfer failed ({type(exc).__name__}).") from None
        if not response.is_success:
            raise WorkflowError(f"WebDAV upload failed (HTTP {response.status_code}).")
        return "/" + "/".join(target_parts), destination_url


def _save_download(store: Any, download: Download, **updates: Any) -> Download:
    current = store.get_download(download.id)
    if current is None:
        raise WorkflowError("Download was removed from the queue.")
    updated = current.model_copy(
        update={"updated_at": datetime.now(), **updates}
    )
    store.set_download(updated)
    return updated


async def process_download(
    download_id: str,
    *,
    store: Any = storage,
    torbox_client: Any = None,
    webdav_client: Any = None,
) -> None:
    download = store.get_download(download_id)
    if download is None or download.status in {"completed", "failed"}:
        return

    try:
        async with httpx.AsyncClient() as client:
            provider = torbox_client or TorBoxClient(
                client,
                settings.torbox_api_key.get_secret_value(),
                settings.torbox_base_url,
            )
            destination = webdav_client or WebDAVClient(
                client,
                settings.webdav_url,
                settings.webdav_username,
                settings.webdav_password.get_secret_value()
                if settings.webdav_password
                else None,
                settings.webdav_remote_path,
            )

            if download.status == "pending":
                download = _save_download(store, download, status="debridding")
            if not download.provider_id:
                provider_type, provider_id = await provider.submit(download)
                download = _save_download(
                    store,
                    download,
                    status="debridding",
                    provider_id=provider_id,
                    provider_type=provider_type,
                )

            def save_progress(progress: float) -> None:
                if download.status == "debridding":
                    bounded_progress = max(0, min(100, progress))
                    _save_download(store, download, progress=bounded_progress)

            item = await provider.wait_until_ready(
                download.provider_type,
                download.provider_id,
                settings.debrid_poll_interval_seconds,
                settings.debrid_poll_timeout_seconds,
                save_progress,
            )
            files = item.get("files") or []
            if not files:
                files = [{"id": 0, "name": download.filename or item.get("name") or "download"}]

            download = _save_download(
                store,
                download,
                status="ready",
                progress=100,
            )
            download = _save_download(store, download, status="transferring")
            transferred_files = list(download.transferred_files)
            first_url = download.file_url
            for file_data in files:
                file_id = int(file_data.get("id", 0))
                file_name = file_data.get("name") or file_data.get("short_name") or "download"
                if len(files) == 1 and download.filename:
                    file_name = download.filename
                file_url = await provider.get_download_url(
                    download.provider_type, download.provider_id, file_id
                )
                remote_path, destination_url = await destination.upload(file_url, file_name)
                transferred_files.append(remote_path)
                if first_url is None:
                    first_url = destination_url
                download = _save_download(
                    store,
                    download,
                    transferred_files=transferred_files,
                    file_url=first_url,
                    destination_path=destination.remote_path,
                )

            _save_download(store, download, status="completed", progress=100)
    except WorkflowError as exc:
        current = store.get_download(download_id)
        if current is not None:
            _save_download(store, current, status="failed", error_message=str(exc))
    except Exception as exc:
        current = store.get_download(download_id)
        if current is not None:
            _save_download(
                store,
                current,
                status="failed",
                error_message=f"Unexpected workflow error ({type(exc).__name__}).",
            )
