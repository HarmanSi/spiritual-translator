"""
Web version of the translator.

Serves a simple webpage (static/index.html) that captures your microphone in
the browser and streams the audio to this server over a WebSocket. This server
feeds that audio into Azure Speech Translation (same as the local version) and
streams the English translation back to the page in real time, plus optionally
pushes each finalized line into your Google Doc.

Run locally with:
    py -3.9 -m uvicorn server:app --reload --port 8000
Then open http://localhost:8000 in your browser.

For hosting on the web, see the README section "Hosting on the web (Render)".
"""

import os
import asyncio
import datetime
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

load_dotenv()

SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_REGION = os.environ.get("SPEECH_REGION")
GOOGLE_DOC_ID = os.environ.get("GOOGLE_DOC_ID")

CANDIDATE_LANGUAGES = ["hi-IN", "pa-IN", "en-US"]
TARGET_LANGUAGE = "en"

if not SPEECH_KEY or not SPEECH_REGION:
    raise RuntimeError("Please set SPEECH_KEY and SPEECH_REGION as environment variables.")

TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "transcripts")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)

app = FastAPI()


@app.get("/")
def index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "static", "index.html"))


app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")), name="static")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    loop = asyncio.get_event_loop()

    # A fresh transcript file + recognizer per browser session/connection
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    transcript_path = os.path.join(TRANSCRIPT_DIR, f"transcript_{timestamp}.txt")

    stream_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
    push_stream = speechsdk.audio.PushAudioInputStream(stream_format)
    audio_config = speechsdk.audio.AudioConfig(stream=push_stream)

    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=SPEECH_KEY, region=SPEECH_REGION
    )
    translation_config.speech_recognition_language = CANDIDATE_LANGUAGES[0]
    translation_config.add_target_language(TARGET_LANGUAGE)
    translation_config.set_property(
        property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
        value="Continuous",
    )

    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=CANDIDATE_LANGUAGES
    )

    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect_config,
    )

    # Boost recognition accuracy for spiritual/religious vocabulary (see phrases.txt)
    phrases_file = os.path.join(os.path.dirname(__file__), "phrases.txt")
    if os.path.exists(phrases_file):
        try:
            grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
            with open(phrases_file, "r", encoding="utf-8") as f:
                for line in f:
                    phrase = line.strip()
                    if phrase and not phrase.startswith("#"):
                        grammar.addPhrase(phrase)
        except Exception as e:
            print(f"(Skipping custom vocabulary boost - not critical: {e})")

    google_docs_writer = None
    if GOOGLE_DOC_ID:
        from google_docs_writer import GoogleDocsWriter
        try:
            google_docs_writer = GoogleDocsWriter(GOOGLE_DOC_ID)
        except Exception as e:
            print(f"(Google Docs sync disabled for this session: {e})")

    def send_to_client(payload):
        try:
            asyncio.run_coroutine_threadsafe(websocket.send_json(payload), loop)
        except Exception:
            pass

    def on_recognizing(evt):
        translation = evt.result.translations.get(TARGET_LANGUAGE, "")
        if translation:
            send_to_client({"type": "interim", "text": translation})

    def on_recognized(evt):
        translation = evt.result.translations.get(TARGET_LANGUAGE, "")
        if not translation:
            return
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] {translation}"
        send_to_client({"type": "final", "text": line})
        with open(transcript_path, "a", encoding="utf-8") as f:
            f.write(line + "\n\n")
        if google_docs_writer:
            google_docs_writer.enqueue_line(line)

    recognizer.recognizing.connect(on_recognizing)
    recognizer.recognized.connect(on_recognized)
    recognizer.start_continuous_recognition()

    try:
        while True:
            data = await websocket.receive_bytes()
            push_stream.write(data)
    except WebSocketDisconnect:
        pass
    finally:
        push_stream.close()
        recognizer.stop_continuous_recognition()
        if google_docs_writer:
            google_docs_writer.stop()