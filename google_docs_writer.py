"""
Handles authenticating with Google and appending text to a Google Doc in real time.

First run: opens a browser window asking you to log in and approve access.
After that, it reuses a saved token.json so you won't need to log in again
(until the token expires, which it'll auto-refresh).

Runs the actual network calls on a background thread with a queue, so a slow
network moment never blocks or delays the live captioning happening in main.py.
"""

import os
import threading
import queue

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/documents"]

BASE_DIR = os.path.dirname(__file__)
CREDENTIALS_PATH = os.environ.get("GOOGLE_CREDENTIALS_PATH", os.path.join(BASE_DIR, "credentials.json"))
TOKEN_PATH = os.environ.get("GOOGLE_TOKEN_PATH", os.path.join(BASE_DIR, "token.json"))


class GoogleDocsWriter:
    def __init__(self, document_id):
        self.document_id = document_id
        self.service = self._authenticate()
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._worker = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker.start()

    def _authenticate(self):
        creds = None
        if os.path.exists(TOKEN_PATH):
            creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif os.environ.get("GOOGLE_HEADLESS", "").lower() == "true":
                raise RuntimeError(
                    "No valid Google token found for headless/server mode. "
                    "Run main.py or server.py locally once first to generate token.json via "
                    "the browser login, then upload that token.json to the server."
                )
            else:
                if not os.path.exists(CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Missing {CREDENTIALS_PATH}. Download it from Google Cloud Console "
                        "(see README section 'Google Docs live sync setup')."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_PATH, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())

        return build("docs", "v1", credentials=creds)

    def enqueue_line(self, text):
        """Call this from the main thread - it just queues the line, doesn't block."""
        self._queue.put(text)

    def _worker_loop(self):
        while not self._stop_event.is_set():
            try:
                text = self._queue.get(timeout=0.5)
            except queue.Empty:
                continue
            self._append_to_doc(text)

    def _append_to_doc(self, text):
        try:
            requests = [
                {
                    "insertText": {
                        "endOfSegmentLocation": {"segmentId": ""},
                        "text": text + "\n\n",  # blank line after each entry
                    }
                }
            ]
            self.service.documents().batchUpdate(
                documentId=self.document_id, body={"requests": requests}
            ).execute()
        except Exception as e:
            print(f"\n(Google Docs sync skipped one line due to an error: {e})")

    def stop(self):
        self._stop_event.set()
        self._worker.join(timeout=2)
