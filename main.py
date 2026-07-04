"""
Real-time Hindi / Punjabi / broken-English speech -> English text translator.
Built for spiritual talks, satsang, kirtan commentary, etc.

How it works:
- Listens on your microphone continuously.
- Auto-detects which of Hindi / Punjabi / English is being spoken, sentence by sentence
  (this is Azure's "continuous language identification").
- Translates whatever it hears into English text in near real-time.
- Prints live "in-progress" text as it's being spoken, then a finalized line when
  a sentence/pause completes.
- Saves everything to a timestamped transcript file in transcripts/.
"""

import os
import sys
import time
import datetime
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.environ.get("SPEECH_KEY")
SPEECH_REGION = os.environ.get("SPEECH_REGION")
GOOGLE_DOC_ID = os.environ.get("GOOGLE_DOC_ID")  # optional - only needed for live Google Docs sync

if not SPEECH_KEY or not SPEECH_REGION:
    print("ERROR: Please set SPEECH_KEY and SPEECH_REGION in a .env file (see .env.example).")
    sys.exit(1)

google_docs_writer = None
if GOOGLE_DOC_ID:
    from google_docs_writer import GoogleDocsWriter
    print("Connecting to Google Docs (a browser window may open for login on first run)...")
    google_docs_writer = GoogleDocsWriter(GOOGLE_DOC_ID)
    print("Connected. Live translation will also be pushed to your Google Doc.")

# The languages we expect to hear. Azure needs full locale codes.
# Feel free to add more, e.g. "en-IN" if speakers use Indian-English pronunciation heavily.
CANDIDATE_LANGUAGES = ["hi-IN", "pa-IN", "en-US"]

TARGET_LANGUAGE = "en"  # English output

TRANSCRIPT_DIR = os.path.join(os.path.dirname(__file__), "transcripts")
os.makedirs(TRANSCRIPT_DIR, exist_ok=True)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
transcript_path = os.path.join(TRANSCRIPT_DIR, f"transcript_{timestamp}.txt")


def build_recognizer():
    translation_config = speechsdk.translation.SpeechTranslationConfig(
        subscription=SPEECH_KEY,
        region=SPEECH_REGION,
    )
    translation_config.speech_recognition_language = CANDIDATE_LANGUAGES[0]
    translation_config.add_target_language(TARGET_LANGUAGE)

    # Continuous language identification: lets the spoken language change
    # between sentences throughout the whole session.
    translation_config.set_property(
        property_id=speechsdk.PropertyId.SpeechServiceConnection_LanguageIdMode,
        value="Continuous",
    )

    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=CANDIDATE_LANGUAGES
    )

    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    recognizer = speechsdk.translation.TranslationRecognizer(
        translation_config=translation_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect_config,
    )
    return recognizer


def add_spiritual_vocabulary(recognizer):
    """
    Optional: boosts recognition accuracy for spiritual/religious terms that
    generic speech models often mis-hear (names, Sanskrit/Punjabi/Gurmukhi terms, etc).
    Edit phrases.txt to add your own words/phrases (one per line).
    """
    phrases_file = os.path.join(os.path.dirname(__file__), "phrases.txt")
    if not os.path.exists(phrases_file):
        return
    try:
        grammar = speechsdk.PhraseListGrammar.from_recognizer(recognizer)
        with open(phrases_file, "r", encoding="utf-8") as f:
            for line in f:
                phrase = line.strip()
                if phrase and not phrase.startswith("#"):
                    grammar.addPhrase(phrase)
        print(f"Loaded custom vocabulary from {phrases_file}")
    except Exception as e:
        print(f"(Skipping custom vocabulary boost - not critical: {e})")


def write_line(text):
    with open(transcript_path, "a", encoding="utf-8") as f:
        f.write(text + "\n\n")  # blank line after each entry


def main():
    recognizer = build_recognizer()
    add_spiritual_vocabulary(recognizer)

    done = False

    def on_recognizing(evt):
        # Live, in-progress translation - overwrite the same console line
        translation = evt.result.translations.get(TARGET_LANGUAGE, "")
        if translation:
            sys.stdout.write("\r" + " " * 100 + "\r")  # clear line
            sys.stdout.write(f"... {translation}")
            sys.stdout.flush()

    def on_recognized(evt):
        translation = evt.result.translations.get(TARGET_LANGUAGE, "")
        if not translation:
            return
        detected_lang = evt.result.properties.get(
            speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult,
            "unknown",
        )
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        line = f"[{ts}] ({detected_lang}) {translation}"
        sys.stdout.write("\r" + " " * 100 + "\r")  # clear the "..." line
        print(line)
        write_line(line)
        if google_docs_writer:
            google_docs_writer.enqueue_line(line)

    def on_canceled(evt):
        print(f"\nCANCELED: {evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {evt.error_details}")
        nonlocal done
        done = True

    def on_session_stopped(evt):
        nonlocal done
        done = True

    recognizer.recognizing.connect(on_recognizing)
    recognizer.recognized.connect(on_recognized)
    recognizer.canceled.connect(on_canceled)
    recognizer.session_stopped.connect(on_session_stopped)

    print("=" * 60)
    print("Listening... speak in Hindi, Punjabi, or English.")
    print(f"Transcript is being saved to: {transcript_path}")
    print("Press Ctrl+C to stop.")
    print("=" * 60)

    recognizer.start_continuous_recognition()

    try:
        while not done:
            time.sleep(0.3)
    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        recognizer.stop_continuous_recognition()
        if google_docs_writer:
            google_docs_writer.stop()
        print(f"\nDone. Full transcript saved at: {transcript_path}")


if __name__ == "__main__":
    main()
