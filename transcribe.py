import os
import argparse
from pathlib import Path
from sarvamai import SarvamAI


# ============================================================
# Command-line arguments
# ============================================================

parser = argparse.ArgumentParser(
    description="Transcribe audio using Saaras v4"
)

parser.add_argument(
    "audio_file",
    help="Audio file to transcribe",
)

args = parser.parse_args()

audio_file = Path(args.audio_file)

if not audio_file.exists():
    raise FileNotFoundError(
        f"Audio file not found: {audio_file}"
    )


# ============================================================
# Sarvam client
# ============================================================

client = SarvamAI(
    api_subscription_key=os.environ["SARVAM_API_KEY"],
)


# ============================================================
# Create transcription job
# ============================================================

job = client.speech_to_text_job.create_job(
    model="saaras:v4",
    language_code="hi-IN",
    mode="translit",

    keyterms=[
        "Cloud Practitioner",
        "CloudOps",
        "AWS",
        "OpenStack",
        "LinkedIn Learning",
        "DaVinci Resolve",
    ],

    with_timestamps=True,
)

print(f"Job created: {job.job_id}")


# ============================================================
# Upload audio
# ============================================================

job.upload_files(
    file_paths=[str(audio_file)]
)

print(f"Uploaded: {audio_file}")


# ============================================================
# Start transcription
# ============================================================

job.start()

print("Transcription started...")


# ============================================================
# Wait until complete
# ============================================================

status = job.wait_until_complete()

print(
    f"Job completed with state: "
    f"{status.job_state}"
)


# ============================================================
# Output directory
# ============================================================

output_dir = (
    Path("outputs")
    / audio_file.stem
)

output_dir.mkdir(
    parents=True,
    exist_ok=True,
)


# ============================================================
# Download raw Saaras JSON
# ============================================================

job.download_outputs(
    output_dir=str(output_dir)
)

print()
print("==============================")
print("Transcription complete!")
print("==============================")
print(f"JSON saved in: {output_dir}")
