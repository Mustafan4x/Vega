"""Production server entry point.

``trader-serve`` (declared in ``pyproject.toml`` ``[project.scripts]``) launches
uvicorn with the ``Server`` header disabled, so the runtime stack is not
fingerprinted by responses. Host and port are overridable via env so the
Render deployment can bind to whatever Render provides.
"""

from __future__ import annotations

import os


def main() -> None:
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "8000")),
        server_header=False,
        proxy_headers=True,
        forwarded_allow_ips=os.environ.get("FORWARDED_ALLOW_IPS", "127.0.0.1"),
        access_log=False,
    )


if __name__ == "__main__":
    main()
