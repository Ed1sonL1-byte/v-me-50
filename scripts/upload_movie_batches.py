"""Upload prepared movie batches through a temporary token-gated RLS policy."""

import json
import time
from pathlib import Path

import httpx


DATA = Path("data")


def main() -> None:
    auth = json.loads((DATA / "import_auth.json").read_text())
    manifest = json.loads((DATA / "import_batches/manifest.json").read_text())
    checkpoint = DATA / "import_checkpoint.json"
    completed = set(json.loads(checkpoint.read_text())) if checkpoint.exists() else set()
    headers = {
        "apikey": auth["publishable_key"],
        "Authorization": f"Bearer {auth['publishable_key']}",
        "x-import-token": auth["import_token"],
        "Prefer": "resolution=ignore-duplicates,return=minimal",
    }
    url = "https://cgnkdgkzmnsxojnxjbzj.supabase.co/rest/v1/movies"
    with httpx.Client(timeout=120, headers=headers) as client:
        for index, item in enumerate(manifest["batches"]):
            if index in completed:
                continue
            path = DATA / "import_batches" / item["file"]
            records = json.loads(path.read_text())
            for attempt in range(4):
                try:
                    response = client.post(url, json=records)
                    response.raise_for_status()
                    break
                except (httpx.HTTPError, httpx.TimeoutException) as exc:
                    if attempt == 3 or (
                        isinstance(exc, httpx.HTTPStatusError)
                        and exc.response.status_code not in {408, 429, 500, 502, 503, 504}
                    ):
                        detail = exc.response.text[:500] if isinstance(exc, httpx.HTTPStatusError) else str(exc)
                        raise RuntimeError(f"Batch {index} failed: {detail}") from exc
                    time.sleep(2 ** attempt)
            completed.add(index)
            checkpoint.write_text(json.dumps(sorted(completed)))
            if (index + 1) % 10 == 0 or index + 1 == len(manifest["batches"]):
                print(f"uploaded {index + 1}/{len(manifest['batches'])} batches", flush=True)


if __name__ == "__main__":
    main()
