"""Development entry point. Run: python run.py"""
import threading
import time
import webbrowser

import uvicorn

HOST = "localhost"
PORT = 8000
DOCS_URL = f"http://{HOST}:{PORT}/docs"


def _open_browser() -> None:
    time.sleep(1.5)  # wait for uvicorn to finish binding
    webbrowser.open(DOCS_URL)


if __name__ == "__main__":
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT, reload=True)
