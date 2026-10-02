# Hinglish Subtitle Generator

> **Before you start:** Create an account on [Sarvam](https://www.sarvam.ai/), generate an API key from your account, and set up billing on their website before running transcription. You will use this API key during setup below.

Turn a video or audio recording into Hinglish subtitles written in English letters (Roman script), such as `Aaj hum AWS ke baare mein baat karenge.`

This guide starts from zero. The commands below are for **macOS Terminal**. Windows users need a Bash-compatible environment and different installation steps; do not paste these setup commands into Windows Command Prompt.

## What happens to your recording?

```text
Video → WAV audio → Sarvam transcription → JSON transcript → SRT subtitles
```

1. `audio_extract.sh` uses FFmpeg on your computer to extract audio.
2. `transcribe.py` uploads audio to Sarvam's cloud service and downloads a timed transcript.
3. `captions.py` turns that transcript into an SRT subtitle file on your computer.
4. You import the SRT into a video editor or a platform that supports subtitle uploads, then review it.

**Before transcription:** you need internet access and your own Sarvam API key. Check your account's current billing and available credits. Only upload recordings you are allowed to send to this service. Audio extraction and caption generation run locally and do not need an API key.

This project creates subtitle files. It does not automatically add visible captions to a video, style them, or publish anything.

## A few terms

| Term | Meaning |
| --- | --- |
| Terminal | The macOS app where you type commands. |
| Command | An instruction you paste into Terminal and run by pressing Return. |
| Folder path | The location of a folder or file on your computer. |
| Python | The software that runs the two `.py` scripts. |
| FFmpeg | The software that extracts audio from video. |
| Virtual environment | A separate place for this project's Python packages. |
| API key | A private credential that lets the script use your Sarvam account. |
| WAV | An audio file format. |
| JSON | The downloaded transcript, including text and timing information. |
| SRT | A subtitle file containing caption text and start/end times. |

## Files in this project

| File or folder | Purpose |
| --- | --- |
| `audio_extract.sh` | Extracts the first audio track as mono, 16 kHz, 16-bit WAV. |
| `transcribe.py` | Runs a Sarvam batch transcription job with `saaras:v4`, `hi-IN`, Roman-script `translit` mode, and timestamps. |
| `captions.py` | Generates one-line or two-line SRT captions from Sarvam JSON. |
| `requirement.txt` | The Python dependency list. The filename is singular: **requirement**, not requirements. |
| `Apple_Pay_In_India - 4K.mov` | Included video. |
| `audio/Apple_Pay_In_India - 4K.wav` | Included extracted audio. |
| `outputs/day8/` | Example transcript and subtitle files. |
| `outputs/Apple_Pay_In_India - 4K/` | Another example transcript and one-line subtitle file. |
| `.git/` and `.DS_Store` | Git history and macOS metadata; not needed for running subtitles. |

## First-time setup

Do this once on each computer.

### 1. Open Terminal

Press **Command + Space**, type **Terminal**, and press **Return**.

Copy only the text inside each command box. Run one command at a time and wait for it to finish. Do not type Markdown markers such as the triple backticks.

### 2. Clone the repository and open its folder

On the repository's GitHub page, click **Code**, select **HTTPS**, and copy the repository URL. In Terminal, type `git clone ` (with a space), paste that URL, and press Return. Git downloads a copy into a new folder in your current location.

If macOS asks you to install command-line developer tools when you run Git, complete that installation and retry. If you already cloned the repository, skip cloning again.

From the folder where you ran the clone command, enter the downloaded project folder:

```bash
cd hinglish_sub
```

This assumes the downloaded folder is named `hinglish_sub`; use its actual name if different. The location depends on where **you** cloned it.

If you are unsure where it is, find the project folder in Finder, type `cd ` (including the space) in Terminal, drag the folder into Terminal, and press Return. This inserts your own folder path.

Check your location and files:

```bash
pwd
ls
```

`pwd` should show your `hinglish_sub` folder. `ls` should show `transcribe.py`, `captions.py`, `audio_extract.sh`, and `requirement.txt`.

**Keep filenames in double quotes when they contain spaces.** All examples use quotes so that names like `My Video.mov` work.

### 3. Install Python

Check whether Python is already available:

```bash
python3 --version
```

If you get `command not found`, install a stable Python 3 release using the macOS installer from [Python's official downloads page](https://www.python.org/downloads/macos/). Follow the installer, reopen Terminal, return to the project folder, and check again.

### 4. Install FFmpeg

Check first:

```bash
ffmpeg -version
```

If it prints version information, continue to the next step.

Otherwise, install Homebrew using the instructions on [the official Homebrew website](https://brew.sh/). Follow its final “Next steps” instructions so the `brew` command becomes available. Then run:

```bash
brew install ffmpeg
ffmpeg -version
```

The installation command is documented by [Homebrew's FFmpeg package page](https://formulae.brew.sh/formula/ffmpeg.html).

### 5. Create the Python environment and install packages

A virtual environment keeps the project's packages together in their own folder. Python includes the tool to create one; you do not need another environment manager.

From the project folder, create an environment named `.venv`, activate it, and install the packages listed in `requirement.txt`:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirement.txt
```

On macOS, the installed Python 3 command is usually `python3`, so it is used to create the environment. If your installation provides `python` instead, use `python -m venv .venv`. Here, `.venv` is the environment name; keep that name to follow the remaining commands exactly.

Create the environment once. Activate it again whenever you open a new Terminal session to work on this project.

After activation, Terminal will usually show `(.venv)` near its prompt. From this point on, use `python` as shown below. The dependency file pins exact package versions; stop if installation reports an error rather than assuming it worked.

Check the Sarvam package:

```bash
python -c "from sarvamai import SarvamAI; print('Sarvam package is ready')"
```

### 6. Get and set your Sarvam API key

Use [Sarvam's official documentation](https://docs.sarvam.ai/) to access its account/API-key setup. Keep your key private. Do not put it into these scripts, the README, screenshots, or Git.

In macOS's default zsh Terminal, run this command, paste your key at the prompt, and press Return:

```bash
read -s "SARVAM_API_KEY?Paste your Sarvam API key, then press Return: "
export SARVAM_API_KEY
```

The key is hidden while you paste/type it. To check its value, run:

```bash
echo $SARVAM_API_KEY
```

For example, if you set the dummy value `Thisisatest`, the output would be:

```text
Thisisatest
```

A blank line means the variable is empty or not set. This command displays your key, so keep that output out of screenshots and shared logs. `Thisisatest` is only an example, not a working API key.

This only checks that the value exists; it does not validate it with Sarvam. The key is set for this Terminal session. Repeat this step after opening a new Terminal window. The scripts do not automatically read a `.env` file.

## Practice first: create captions without uploading audio

You can check caption generation with the included `day8` transcript. This step does not contact Sarvam.

Run this from the project folder with your Python environment active:

```bash
python captions.py "outputs/day8/day8.wav.json"
```

The script asks you to choose a layout:

```text
Choose caption layout:

1. One line  - Vertical video / Reels / Shorts
2. Two lines - Horizontal video / YouTube

Enter 1 or 2:
```

Type `1` or `2` and press Return. When generation finishes, you will see `Caption generation complete!` and the saved SRT path:

- Choose `1`: `outputs/day8/day8_1-line.srt`.
- Choose `2`: `outputs/day8/day8_2-line.srt`.

Open that folder in Finder:

```bash
open "outputs/day8"
```

The existing `day8.srt` is an older example; the current script names two-line output `day8_2-line.srt`.

## Runbook: make subtitles for a new video

A runbook is a repeatable set of steps. Follow these in order for each recording.

### Step 1. Prepare your session and input

Open Terminal and enter your cloned project folder. You can type `cd `, drag the folder from Finder into Terminal, and press Return. Then activate the environment:

```bash
source .venv/bin/activate
```

If you are still in the parent folder where you cloned the repository, `cd hinglish_sub` enters it. Set the API key as explained above if this is a new Terminal session.

Copy your video into the project folder using Finder. For this walkthrough, name the copy `My Video.mov`. Substitute your actual filename throughout if you keep another name. Prefer a unique name for each recording to avoid mixing outputs from different videos.

### Step 2. Extract the audio

```bash
bash audio_extract.sh "My Video.mov"
```

Expected final message:

```text
Audio extracted successfully:
My Video.wav
```

The WAV is saved in **Terminal's current folder**, even if the input file lives elsewhere. The script selects the first audio track. Check that it contains the speech you want.

If a WAV with that name already exists, FFmpeg may ask whether to overwrite it. Answer `n` to keep it, or `y` only if you intend to replace it. If you already have the intended WAV, you can skip extraction and use it in Step 3.

### Step 3. Transcribe the WAV

**This step uploads the audio to Sarvam and may use billable credits.**

```bash
python transcribe.py "My Video.wav"
```

You should see a job ID, an upload message, and `Transcription started...`. Wait for completion. Do not close Terminal while it is processing.

The script saves downloads under:

```text
outputs/My Video/
```

Check the downloaded filename:

```bash
ls "outputs/My Video"
```

The included examples use names such as `My Video.wav.json`. Use the **actual downloaded JSON filename** in the next step. A final printed message alone is not enough: confirm a JSON file exists and that caption generation can read it.

The code requests Roman-script output using `translit`, as described in [Sarvam's speech-to-text documentation](https://docs.sarvam.ai/api/api-guides-tutorials/speech-to-text/overview).

### Step 4. Generate the caption layout

Run the caption script using the JSON filename downloaded in Step 3:

```bash
python captions.py "outputs/My Video/My Video.wav.json"
```

The script asks you to choose a layout:

```text
Choose caption layout:

1. One line  - Vertical video / Reels / Shorts
2. Two lines - Horizontal video / YouTube

Enter 1 or 2:
```

Type your choice and press Return:

- Enter `1` for vertical videos such as Reels or Shorts. Output: `outputs/My Video/My Video_1-line.srt`.
- Enter `2` for horizontal videos such as regular YouTube videos. Output: `outputs/My Video/My Video_2-line.srt`.

Wait for `Caption generation complete!` and check the printed SRT path. To create the other layout, run the same command again and select the other option. Both layouts use the same JSON, so no new transcription is needed.

### Step 5. Locate and review your subtitles

```bash
open "outputs/My Video"
```

Import the chosen SRT through your video editor's subtitle import feature. Exact menu names depend on the editor and version. Match the subtitle track to the same recording used for transcription; trimming or rearranging the video afterwards can put captions out of sync.

Play the entire video and check:

- Names, Hindi spelling in Roman script, English terms, and numbers are correct.
- Captions appear when the relevant speech is heard.
- Each caption stays on screen long enough to read.
- Line breaks fit the screen and do not cover important content.
- Silence does not show unwanted text.

Correct text and timing in your editor before exporting. SRT stores text and timing; font, colour, position, and animation are chosen in the editor.

### Step 6. Finish and keep the useful files

Keep the original video, JSON, and final SRT together. If you edit the SRT, save a separately named final copy: rerunning `captions.py` **overwrites its generated SRT with the same name without asking**.

When finished:

```bash
unset SARVAM_API_KEY
deactivate
```

`deactivate` leaves the environment installed for next time.

## Example using the included video

The folder already includes `audio/Apple_Pay_In_India - 4K.wav`, so you can skip extraction if that audio is the version you want.

To generate subtitles from its already downloaded JSON, with no new API call:

```bash
python captions.py "outputs/Apple_Pay_In_India - 4K/Apple_Pay_In_India - 4K.wav.json"
```

Enter `1` for one-line captions or `2` for two-line captions when prompted. The SRT is saved in `outputs/Apple_Pay_In_India - 4K/` as `Apple_Pay_In_India - 4K_1-line.srt` or `Apple_Pay_In_India - 4K_2-line.srt`, depending on your choice.

If you want to create a new transcription from the included audio instead:

```bash
python transcribe.py "audio/Apple_Pay_In_India - 4K.wav"
```

That command uploads the audio to Sarvam and may use billable credits. Its downloads go into `outputs/Apple_Pay_In_India - 4K/`; inspect that folder before choosing a JSON filename. The output folder uses the audio filename without its extension, even though the input is stored in `audio/`.

## What caption generation can and cannot do

| Setting | One-line mode | Two-line mode |
| --- | --- | --- |
| Intended use | Vertical video | Horizontal video |
| Intended maximum lines | 1 | 2 |
| Character target per line | 34 | 38 |
| Word limit used when splitting | 7 per caption | 9 per caption |

These are formatting rules, not a guarantee that every generated caption fits perfectly. A very long word or text that cannot be split into two suitable lines can exceed the intended width.

The script divides each transcript segment's duration between chunks according to word count. It does **not** align every caption to exact word-level speech timing. Short captions may appear very briefly. Although the profiles define minimum and target durations, those values are not enforced by the current splitting function; the maximum-duration setting helps estimate chunk count rather than guaranteeing a strict duration limit.

Text cleanup changes `day eight` to `day 8` (number words one through twenty), `sixty` to `60`, and `60 days` to `60-day`. Review whether those changes make sense in your recording.

The transcription script includes hints for terms such as AWS, OpenStack, CloudOps, Cloud Practitioner, LinkedIn Learning, and DaVinci Resolve. Hints improve context but do not guarantee correct spelling.

## Troubleshooting

| Problem | What to do |
| --- | --- |
| `cd: no such file or directory` | Use your actual folder path. Drag the folder from Finder after typing `cd `, then press Return. |
| `python3: command not found` | Complete Python installation, reopen Terminal, and check `python3 --version`. |
| `ffmpeg: command not found` | Complete FFmpeg installation and Homebrew's PATH instructions. Reopen Terminal if needed. |
| `brew: command not found` | Complete Homebrew installation and its “Next steps” instructions. |
| `No module named 'sarvamai'` | Activate `.venv` and run `python -m pip install -r requirement.txt` using that environment. |
| Package installation says a pinned version is unavailable | Check internet access and the complete error. The dependency file may need a maintainer update; do not silently substitute versions and assume compatibility. |
| `KeyError: 'SARVAM_API_KEY'` | Set and export the key in the same Terminal window that runs transcription. |
| Authentication / 401 / 403 error | Check the key and account access in Sarvam. Do not post your key when asking for help. |
| Credit, quota, or rate-limit error | Check the account dashboard and error message before retrying. Repeated transcription runs can create new jobs and charges. |
| `File not found` or `can't open file` | Confirm your current folder with `pwd`, inspect filenames with `ls`, and quote paths containing spaces. |
| FFmpeg cannot find an audio stream | The file may have no audio track. Try a recording that contains speech. |
| Existing WAV / overwrite prompt | Keep the existing file unless you intend to replace it. Use a unique input basename for another recording. |
| Transcription failed, appears stuck, or was interrupted | Keep the printed job ID and check its state with Sarvam. This script has no saved-job resume command; rerunning starts a new job. |
| No JSON after transcription | Check the printed job state, service errors, and the actual `outputs/<audio-name>/` folder. Do not proceed with an unrelated old JSON. |
| `KeyError: 'timestamps'` or another timestamp field | You may have selected a different JSON format or an error response. Use the timed transcript produced by this project. |
| Subtitle text/timing is wrong | Review and correct it in your editor. Automatic transcription and approximate caption timing need human checking. |
| Corrected SRT changed after rerunning | Generated SRTs are overwritten. Keep edited final versions under separate filenames. |

For help, share the command used, the error text, and whether the expected files exist. Remove API keys and private transcript content before sharing.

## Verification notes

This README was checked against the current scripts and included transcript/subtitle files. Both caption layouts were generated successfully from a temporary copy of the `day8` JSON, and the audio extraction script passed a Bash syntax check. Fresh dependency installation, actual media conversion, cloud transcription, billing, and editor import were not tested during this documentation update.
