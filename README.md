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

## Running it as a website instead of a terminal script

This project now includes a web version: `server.py` (backend) + `static/index.html`
(a page that captures your mic in the browser and shows live English text).

### Try it locally first

```bash
py -3.9 -m pip install -r requirements.txt
py -3.9 -m uvicorn server:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser, click **Start Listening**, and
allow microphone access when your browser asks. You should see live English text
appear, same as the terminal version.

## Hosting on the web (Render)

Render will run `server.py` continuously so you never need to open a terminal or
keep your laptop's Python running — just open a browser tab from anywhere.

### 1. Push this project to GitHub
If you haven't already:
```bash
git init
git add .
git commit -m "initial version"
```
Create a new repo on https://github.com/new, then follow GitHub's instructions to push
(`git remote add origin ...`, `git push -u origin main`).

**Important:** make sure `.env`, `credentials.json`, and `token.json` are NOT in this repo
(the included `.gitignore` already excludes them — just don't force-add them).

### 2. Create the Render service
1. Go to https://render.com and sign up (free, can use your Google/GitHub account).
2. Click **New +** -> **Web Service**.
3. Connect your GitHub account and select this repo.
4. Fill in:
   - **Name**: anything (e.g. `spiritual-translator`)
   - **Region**: closest to you
   - **Runtime**: **Python 3**
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free** to test, or **Starter** (~$7/month) so it doesn't
     go to sleep between uses — free tier spins down after inactivity and takes
     ~30-60 seconds to wake up on the next visit, which isn't great mid-talk.

### 3. Add your secrets
Still on Render, before/after the first deploy, go to your service -> **Environment**:

- Add environment variables:
  - `SPEECH_KEY` = your Azure key
  - `SPEECH_REGION` = your Azure region
  - `GOOGLE_DOC_ID` = your Google Doc ID (only if using Google Docs sync)
  - `GOOGLE_HEADLESS` = `true` (only if using Google Docs sync — this tells the
    server not to try opening a browser login, since there isn't one on a server)
  - `GOOGLE_TOKEN_PATH` = `/etc/secrets/token.json` (only if using Google Docs sync)

- Under **Secret Files** (same Environment page), add a secret file:
  - Filename: `token.json`
  - Contents: paste the entire contents of your local `token.json` (open it with
    Notepad and copy everything). This is the file that was created the first time
    you approved Google access locally — reusing it means the server never needs
    an interactive login.

### 4. Deploy
Click **Create Web Service** (or **Manual Deploy** if it already exists). Render will
install dependencies and start the server. Once it says **Live**, open the URL it
gives you (something like `https://spiritual-translator.onrender.com`) on your phone
or laptop browser, click **Start Listening**, and you're live — no terminal needed.

### Notes
- Every time you open the page and click Start, that's a fresh session — like
  restarting `main.py` each time.
- If you didn't set up Google Docs sync, just skip the `GOOGLE_*` variables entirely —
  the site will still work, showing live text and saving transcripts on the server.
- **Costs**: Render's Starter tier is usually enough for a single continuous live
  session (~$7/month); Azure speech translation billing is unaffected by hosting —
  it's still billed per audio hour as before.

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
