import unittest

import httpx

from api.models import Download
from api.workflow import TorBoxClient, WebDAVClient, WorkflowError, process_download


class MemoryStorage:
    def __init__(self, download: Download):
        self.downloads = {download.id: download}
        self.statuses = [download.status]

    def get_download(self, download_id: str):
        return self.downloads.get(download_id)

    def set_download(self, download: Download):
        self.downloads[download.id] = download
        self.statuses.append(download.status)


class FakeTorBox:
    async def submit(self, download: Download):
        return "torrent", "42"

    async def wait_until_ready(
        self, provider_type, provider_id, poll_interval, timeout, on_progress
    ):
        on_progress(37)
        return {
            "name": "Example release",
            "files": [{"id": 7, "name": "Season 1/episode.mkv"}],
        }

    async def get_download_url(self, provider_type, provider_id, file_id):
        return "https://cdn.example.test/episode.mkv"


class FakeWebDAV:
    remote_path = "/downloads"

    def __init__(self):
        self.uploads = []

    async def upload(self, source_url, file_name):
        self.uploads.append((source_url, file_name))
        return f"/downloads/{file_name}", f"https://dav.example.test/{file_name}"


class DownloadWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_persists_each_success_state_and_uploaded_path(self):
        download = Download(magnet_link="magnet:?xt=urn:btih:abc")
        store = MemoryStorage(download)
        destination = FakeWebDAV()

        await process_download(
            download.id,
            store=store,
            torbox_client=FakeTorBox(),
            webdav_client=destination,
        )

        saved = store.get_download(download.id)
        self.assertEqual(
            [
                "pending",
                "debridding",
                "debridding",
                "debridding",
                "ready",
                "transferring",
                "transferring",
                "completed",
            ],
            store.statuses,
        )
        self.assertEqual("completed", saved.status)
        self.assertEqual(["/downloads/Season 1/episode.mkv"], saved.transferred_files)
        self.assertEqual("/downloads", saved.destination_path)
        self.assertEqual(
            [("https://cdn.example.test/episode.mkv", "Season 1/episode.mkv")],
            destination.uploads,
        )

    async def test_provider_failure_is_persisted(self):
        class FailingTorBox:
            async def submit(self, download):
                raise WorkflowError("TorBox rejected the download.")

        download = Download(url="https://example.test/file.zip")
        store = MemoryStorage(download)

        await process_download(
            download.id,
            store=store,
            torbox_client=FailingTorBox(),
            webdav_client=FakeWebDAV(),
        )

        saved = store.get_download(download.id)
        self.assertEqual("failed", saved.status)
        self.assertEqual("TorBox rejected the download.", saved.error_message)

    async def test_torbox_uses_documented_endpoints_and_response_fields(self):
        requests = []

        def respond(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            if request.url.path.endswith("/torrents/createtorrent"):
                self.assertIn(b"magnet", request.content)
                return httpx.Response(
                    200, json={"success": True, "data": {"torrent_id": 42}}
                )
            if request.url.path.endswith("/torrents/mylist"):
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "data": [
                            {
                                "download_finished": True,
                                "files": [{"id": 7, "name": "episode.mkv"}],
                            }
                        ],
                    },
                )
            return httpx.Response(
                200,
                json={"success": True, "data": "https://cdn.example.test/file"},
            )

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            torbox = TorBoxClient(client, "test-token", "https://api.torbox.app")
            provider_type, provider_id = await torbox.submit(
                Download(magnet_link="magnet:?xt=urn:btih:abc")
            )
            item = await torbox.get_item(provider_type, provider_id)
            url = await torbox.get_download_url(provider_type, provider_id, 7)

        self.assertEqual(("torrent", "42"), (provider_type, provider_id))
        self.assertTrue(item["download_finished"])
        self.assertEqual(7, item["files"][0]["id"])
        self.assertEqual("https://cdn.example.test/file", url)
        self.assertTrue(all(request.headers["authorization"] == "Bearer test-token" for request in requests))
        self.assertEqual("42", requests[1].url.params["id"])
        self.assertEqual("7", requests[2].url.params["file_id"])

    async def test_webdav_streams_files_and_rejects_parent_paths(self):
        uploaded = []

        async def respond(request: httpx.Request) -> httpx.Response:
            if request.method == "PUT":
                uploaded.append(await request.aread())
                return httpx.Response(201)
            if request.method == "GET":
                return httpx.Response(200, content=b"file contents")
            return httpx.Response(201)

        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            destination = WebDAVClient(
                client,
                "https://dav.example.test/root",
                "user",
                "password",
                "/downloads",
            )
            remote_path, destination_url = await destination.upload(
                "https://cdn.example.test/file", "Season 1/episode.mkv"
            )

        self.assertEqual("/downloads/Season 1/episode.mkv", remote_path)
        self.assertEqual(
            "https://dav.example.test/root/downloads/Season%201/episode.mkv",
            destination_url,
        )
        self.assertEqual([b"file contents"], uploaded)
        with self.assertRaises(WorkflowError):
            WebDAVClient._safe_parts("../outside.mkv")


if __name__ == "__main__":
    unittest.main()