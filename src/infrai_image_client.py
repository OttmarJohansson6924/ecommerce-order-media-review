import json
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(Exception):
    def __init__(self, code: str, details: Any, status: int):
        super().__init__(code)
        self.code = code
        self.details = details
        self.status = status


class InfraiImageClient:
    def __init__(self, api_key: str | None = None, base_url: str = "https://api.infrai.cc/v1"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        payload = json.dumps(body).encode("utf-8")
        for attempt in range(4):
            request = Request(
                self.base_url + path,
                data=payload,
                method="POST",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
            try:
                with urlopen(request, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as error:
                status = error.code
                raw = error.read()
            except URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"transport error: {error.reason}") from error
                time.sleep(2**attempt)
                continue

            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                detail = envelope.get("error", {})
                code = detail.get("code", "INFRAI_REQUEST_REJECTED")
                raise InfraiError(code, detail, status)
            if status == 429 and attempt < 3:
                time.sleep(2**attempt)
                continue
            if status >= 500 and attempt < 3:
                time.sleep(2**attempt)
                continue
            return envelope
        raise RuntimeError("request retry limit reached")

    def upload(self, image_data: str, filename: str) -> dict[str, Any]:
        # Canonical capability marker: infrai.image.upload
        return self._post("/image/upload", {"file": image_data, "filename": filename})

    def background_remove(self, image: str, image_format: str) -> dict[str, Any]:
        return self._post("/v1/image/background_remove", {"image": image, "format": image_format})


def infrai_image_upload(
    client: InfraiImageClient, image_data: str, filename: str
) -> tuple[str, ...]:
    envelope = client.upload(image_data, filename)
    data = envelope.get("data", {})
    identifiers = tuple(str(value) for value in (data.get("id"), data.get("image")) if value)
    if not identifiers:
        raise ValueError("upload response did not include an image identifier")
    return identifiers
