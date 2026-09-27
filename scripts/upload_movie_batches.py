"""Upload prepared movie batches through a temporary token-gated RLS policy."""

import argparse
import asyncio
import json
from pathlib import Path

import httpx


DATA = Path("data")


async def upload(args: argparse.Namespace) -> None:
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
    pending = [(i, item) for i, item in enumerate(manifest["batches"]) if i not in completed]
    if args.max_new_batches:
        pending = pending[: args.max_new_batches]
    semaphore = asyncio.Semaphore(args.concurrency)

    async with httpx.AsyncClient(timeout=120, headers=headers, limits=httpx.Limits(max_connections=args.concurrency)) as client:
        async def send(index: int, item: dict) -> None:
            async with semaphore:
                path = DATA / "import_batches" / item["file"]
                records = json.loads(path.read_text())
                for attempt in range(5):
                    try:
                        response = await client.post(url, json=records)
                        response.raise_for_status()
                        break
                    except httpx.HTTPError as exc:
                        retryable = not isinstance(exc, httpx.HTTPStatusError) or exc.response.status_code in {408, 429, 500, 502, 503, 504}
                        if attempt == 4 or not retryable:
                            detail = exc.response.text[:500] if isinstance(exc, httpx.HTTPStatusError) else str(exc)
                            raise RuntimeError(f"Batch {index} failed: {detail}") from exc
                        await asyncio.sleep(2 ** attempt)
                completed.add(index)
                temporary = checkpoint.with_suffix(".tmp")
                temporary.write_text(json.dumps(sorted(completed)))
                temporary.replace(checkpoint)
                if len(completed) % 100 == 0 or len(completed) == len(manifest["batches"]):
                    print(f"uploaded {len(completed)}/{len(manifest['batches'])} batches", flush=True)

        for start in range(0, len(pending), 100):
            await asyncio.gather(*(send(index, item) for index, item in pending[start:start + 100]))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--concurrency", type=int, default=6)
    parser.add_argument("--max-new-batches", type=int, default=0)
    args = parser.parse_args()
    if not 1 <= args.concurrency <= 16 or args.max_new_batches < 0:
        raise ValueError("Use concurrency 1–16 and a nonnegative batch limit.")
    asyncio.run(upload(args))


if __name__ == "__main__":
    main()
