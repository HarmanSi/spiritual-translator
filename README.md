# Spiritual Talk Translator (Hindi/Punjabi/broken English -> English text)

Listens to your microphone in real time and prints English text, no matter whether
the speaker is using Hindi, Punjabi, or broken English (or switching between them
sentence by sentence). Built on Azure AI Speech's real-time Speech Translation service.

Every session is also saved as a timestamped `.txt` transcript in `transcripts/`.

---

## Step 1: Create your Azure Speech resource (one-time setup, ~5 minutes)

1. Go to https://portal.azure.com and sign in (or create a free account).
2. Click **Create a resource** -> search for **"Speech"** -> select **Speech** (by Microsoft) -> **Create**.
3. Fill in:
   - **Subscription**: your subscription
   - **Resource group**: create a new one, name it anything (e.g. `translator-rg`)
   - **Region**: pick one close to you (e.g. `Central India`, `East US`)
   - **Name**: anything (e.g. `spiritual-translator`)
   - **Pricing tier**: choose **Free F0** to start (gives you free monthly audio hours to test with).
     Switch to **Standard S0** later if you outgrow the free tier.
4. Click **Review + Create** -> **Create**. Wait ~1 minute for deployment.
5. Once deployed, click **Go to resource**.
6. In the left sidebar, click **Keys and Endpoint**.
   - Copy **KEY 1**
   - Copy the **Region** (e.g. `centralindia`, `eastus`) — it's shown on that same page.

Keep this tab open, you'll need these two values in Step 3.

## Step 2: Install Python requirements

You need **Python 3.9+** installed. Then, inside this project folder:

```bash
pip install -r requirements.txt
```

If you're on Linux, you may also need the audio driver library first:
```bash
sudo apt-get install libasound2 libssl-dev
```
(macOS and Windows don't need this step.)

## Step 3: Add your Azure credentials

1. Copy `.env.example` to a new file named `.env`
2. Open `.env` and paste in your key + region from Step 1:

```
SPEECH_KEY=paste_your_key_here
SPEECH_REGION=centralindia
```

**Never commit `.env` to a public GitHub repo** — it contains your secret key.
(A `.gitignore` is already included so it won't accidentally get committed.)

## Step 4: Run it

```bash
python main.py
```

Speak normally in Hindi, Punjabi, or English into your mic. You'll see:
- A live "in progress" line (`...`) updating as you speak
- A finalized line once you pause, saved with a timestamp and the detected language, e.g.:

```
[19:42:11] (hi-IN) All beings are one with the divine, this is the essence of the teaching.
[19:42:34] (pa-IN) Today we will talk about seva and humility.
```

Press `Ctrl+C` to stop. Your full transcript is saved in `transcripts/transcript_<date>_<time>.txt`.

## Google Docs live sync setup (optional)

This pushes every finalized translated line straight into a real Google Doc while
you're speaking — great for a shared live-caption doc during an event.

### A. Create the Google Doc
1. Go to https://docs.google.com and create a new blank document (any title).
2. Copy its ID from the URL: `https://docs.google.com/document/d/`**`THIS_PART`**`/edit`

### B. Set up Google Cloud API access (one-time, ~5 minutes)
1. Go to https://console.cloud.google.com and sign in with the same Google account.
2. Click the project dropdown at the top -> **New Project** -> name it anything
   (e.g. `spiritual-translator`) -> **Create**. Make sure it's selected as your active project.
3. In the search bar, type **"Google Docs API"** -> open it -> click **Enable**.
4. Search again for **"Google Drive API"** -> open it -> click **Enable**.
5. In the left menu, go to **APIs & Services -> OAuth consent screen**.
   - User type: **External** -> Create.
   - Fill in app name (anything), your email for support + developer contact -> Save and Continue through the rest (you can skip scopes/test users screens with defaults).
   - On the **Test users** step, click **Add users** and add your own Gmail address. Save.
6. Go to **APIs & Services -> Credentials** -> **+ Create Credentials** -> **OAuth client ID**.
   - Application type: **Desktop app**
   - Name: anything -> **Create**
7. Click **Download JSON** on the credential you just created.
8. Rename the downloaded file to exactly `credentials.json` and place it in this project folder
   (same folder as `main.py`).

### C. Configure and run
1. Open your `.env` file and set:
   ```
   GOOGLE_DOC_ID=paste_the_doc_id_from_step_A
   ```
2. Install the new dependencies (only needed once):
   ```bash
   py -3.9 -m pip install -r requirements.txt
   ```
3. Run the translator as usual:
   ```bash
   py -3.9 main.py
   ```
4. On the very first run, a browser window will pop up asking you to log into Google and
   approve access ("Google hasn't verified this app" is expected and fine here — it's your own
   app/project — click **Advanced -> Go to (your app name)** to proceed, then **Allow**).
5. After approving once, a `token.json` file is saved so you won't need to log in again.

From then on, every finalized translated line appears in your terminal, your local
transcript file, **and** your Google Doc — all in real time, each with a blank line after it.

**Security note:** `credentials.json` and `token.json` both grant access to write to your
Google Docs. Never share them or commit them to a public repo (they're already excluded
via `.gitignore`).

## Customizing recognition for your vocabulary


Edit `phrases.txt` and add any names, terms, or phrases specific to your talks
(gurus' names, specific Sanskrit/Gurmukhi terms, book titles, etc). This nudges
the recognizer to catch them correctly instead of mishearing them — especially
useful for words that don't exist in everyday English/Hindi/Punjabi.

## Notes, limits, and tips

- **Mid-sentence code-switching**: the model detects a language change well when
  the speaker pauses or moves to a new sentence, but it won't catch someone
  switching languages *within* one sentence. In practice this is rarely an issue
  for talks/discourses.
- **Latency**: usually well under a second behind the live speech for the interim
  text, with finalized lines appearing right after a natural pause.
- **Cost**: real-time speech translation is billed per audio hour (roughly $2.50/hour
  for the base service, plus a small add-on for continuous language detection).
  Azure's free tier includes some free hours per month — good for testing and
  small events. Check the current numbers on Azure's pricing page before going live
  with a large event, since pricing can change.
- **Multiple mics / noisy rooms**: for a temple/hall setting, a lapel or handheld
  mic close to the speaker will give far better accuracy than a laptop's built-in mic.
- Want it displayed as live captions on a screen instead of a terminal? That's a
  natural next step (e.g. a simple local webpage) — happy to build that on top of this
  once the core pipeline is working for you.

## Project structure

```
spiritual-translator/
  main.py             <- the translator itself
  requirements.txt    <- Python dependencies
  .env.example        <- template for your credentials
  .gitignore
  phrases.txt          <- your custom spiritual vocabulary
  transcripts/         <- saved transcripts appear here
  README.md
```
