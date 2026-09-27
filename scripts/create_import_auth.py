"""Create an ignored local import token file; print only the SHA-256 token hash."""

import hashlib
import json
import os
import secrets
from pathlib import Path


def main() -> None:
    publishable_key = os.environ["SUPABASE_PUBLISHABLE_KEY"]
    token = secrets.token_urlsafe(48)
    path = Path("data/import_auth.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("Remove the previous import auth file after revoking its policy.")
    path.write_text(json.dumps({"publishable_key": publishable_key, "import_token": token}))
    path.chmod(0o600)
    print(hashlib.sha256(token.encode()).hexdigest())


if __name__ == "__main__":
    main()
