import re
import json
import argparse
from pathlib import Path


# ============================================================
# Caption profiles
# ============================================================

CAPTION_PROFILES = {

    # Vertical video:
    # Instagram Reels / YouTube Shorts / TikTok
    1: {
        "name": "1-line",
        "description": "Vertical / Reels / Shorts",

        "max_lines": 1,
        "max_chars_per_line": 34,
        "max_words": 7,

        "min_duration": 1.0,
        "target_duration": 2.3,
        "max_duration": 3.5,
    },

    # Horizontal video:
    # YouTube / normal landscape video
    2: {
        "name": "2-line",
        "description": "Horizontal / YouTube",

        "max_lines": 2,
        "max_chars_per_line": 38,
        "max_words": 9,

        "min_duration": 1.2,
        "target_duration": 2.5,
        "max_duration": 4.0,
    },
}


# ============================================================
# Number normalization
# ============================================================

DAY_NUMBERS = {
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
}


# ============================================================
# Text cleanup
# ============================================================

def normalize_caption_text(text):

    # --------------------------------------------------------
    # "day eight" -> "day 8"
    # --------------------------------------------------------

    day_pattern = (
        r"\bday\s+("
        + "|".join(DAY_NUMBERS.keys())
        + r")\b"
    )

    def replace_day_number(match):

        number_word = (
            match.group(1).lower()
        )

        return (
            f"day "
            f"{DAY_NUMBERS[number_word]}"
        )

    text = re.sub(
        day_pattern,
        replace_day_number,
        text,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # sixty -> 60
    # --------------------------------------------------------

    text = re.sub(
        r"\bsixty\b",
        "60",
        text,
        flags=re.IGNORECASE,
    )

    # --------------------------------------------------------
    # 60 day / 60 days -> 60-day
    # --------------------------------------------------------

    text = re.sub(
        r"\b60\s+days?\b",
        "60-day",
        text,
        flags=re.IGNORECASE,
    )

    # Remove duplicate spaces
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip()


# ============================================================
# SRT timestamp formatter
# ============================================================

def srt_timestamp(seconds):

    milliseconds = round(
        seconds * 1000
    )

    hours = (
        milliseconds
        // 3_600_000
    )

    milliseconds %= 3_600_000

    minutes = (
        milliseconds
        // 60_000
    )

    milliseconds %= 60_000

    secs = (
        milliseconds
        // 1000
    )

    milliseconds %= 1000

    return (
        f"{hours:02}:"
        f"{minutes:02}:"
        f"{secs:02},"
        f"{milliseconds:03}"
    )


# ============================================================
# Check how much text a caption can contain
# ============================================================

def caption_character_limit(profile):

    return (
        profile["max_chars_per_line"]
        * profile["max_lines"]
    )


# ============================================================
# Smart caption splitter
# ============================================================

def split_caption_text(
    text,
    start,
    end,
    profile,
):

    words = text.strip().split()

    if not words:
        return []

    total_duration = (
        end - start
    )

    total_words = len(words)

    max_words = profile["max_words"]

    max_duration = (
        profile["max_duration"]
    )

    max_chars = (
        caption_character_limit(
            profile
        )
    )

    # --------------------------------------------------------
    # Work out approximately how many chunks are required
    # --------------------------------------------------------

    chunks_by_words = max(
        1,
        (
            total_words
            + max_words
            - 1
        )
        // max_words,
    )

    chunks_by_duration = max(
        1,
        int(
            (
                total_duration
                + max_duration
                - 0.001
            )
            // max_duration
        ),
    )

    total_characters = len(text)

    chunks_by_characters = max(
        1,
        (
            total_characters
            + max_chars
            - 1
        )
        // max_chars,
    )

    number_of_chunks = max(
        chunks_by_words,
        chunks_by_duration,
        chunks_by_characters,
    )

    target_words = max(
        1,
        round(
            total_words
            / number_of_chunks
        ),
    )

    # --------------------------------------------------------
    # Words where breaks often sound natural in Hinglish
    # --------------------------------------------------------

    preferred_breaks = {
        "aur",
        "but",
        "lekin",
        "toh",
        "because",
        "basically",
        "phir",
        "then",
        "so",
    }

    chunks = []

    current = []

    current_chars = 0

    for word in words:

        word_chars = len(word)

        if current:
            projected_chars = (
                current_chars
                + 1
                + word_chars
            )
        else:
            projected_chars = word_chars

        # ----------------------------------------------------
        # If adding this word would make the caption too wide,
        # finish the previous caption first.
        # ----------------------------------------------------

        if (
            current
            and projected_chars > max_chars
        ):
            chunks.append(current)

            current = []
            current_chars = 0

        current.append(word)

        if current_chars:
            current_chars += 1

        current_chars += word_chars

        punctuation_break = (
            word.endswith(
                (
                    ".",
                    "?",
                    "!",
                    ",",
                )
            )
        )

        cleaned_word = (
            word.lower()
            .strip(".,?!")
        )

        natural_break = (
            cleaned_word
            in preferred_breaks
        )

        # ----------------------------------------------------
        # Prefer a natural break once we're around target size
        # ----------------------------------------------------

        if len(current) >= target_words:

            if (
                punctuation_break
                or natural_break
                or len(current) >= max_words
            ):

                chunks.append(
                    current
                )

                current = []

                current_chars = 0

        elif len(current) >= max_words:

            chunks.append(current)

            current = []

            current_chars = 0

    if current:

        chunks.append(current)


    # ========================================================
    # Calculate approximate timestamps
    # ========================================================

    caption_blocks = []

    current_time = start

    words_remaining = sum(
        len(chunk)
        for chunk in chunks
    )

    time_remaining = (
        end - start
    )

    for index, chunk in enumerate(
        chunks
    ):

        chunk_word_count = len(chunk)

        # Last chunk finishes exactly at Saaras timestamp
        if index == len(chunks) - 1:

            chunk_end = end

        else:

            chunk_duration = (
                time_remaining
                * chunk_word_count
                / words_remaining
            )

            chunk_end = (
                current_time
                + chunk_duration
            )

        caption_blocks.append(
            {
                "text": " ".join(chunk),
                "start": current_time,
                "end": chunk_end,
            }
        )

        time_remaining -= (
            chunk_end
            - current_time
        )

        words_remaining -= (
            chunk_word_count
        )

        current_time = (
            chunk_end
        )

    return caption_blocks


# ============================================================
# Caption line formatting
# ============================================================

def format_caption(
    text,
    profile,
):

    max_lines = (
        profile["max_lines"]
    )

    max_chars = (
        profile[
            "max_chars_per_line"
        ]
    )

    # --------------------------------------------------------
    # ONE-LINE MODE
    # --------------------------------------------------------

    if max_lines == 1:

        return text


    # --------------------------------------------------------
    # TWO-LINE MODE
    # --------------------------------------------------------

    if len(text) <= max_chars:

        return text

    words = text.split()

    best_split = None

    best_difference = float(
        "inf"
    )

    for i in range(
        1,
        len(words)
    ):

        line1 = " ".join(
            words[:i]
        )

        line2 = " ".join(
            words[i:]
        )

        if (
            len(line1) <= max_chars
            and
            len(line2) <= max_chars
        ):

            difference = abs(
                len(line1)
                - len(line2)
            )

            if (
                difference
                < best_difference
            ):

                best_difference = (
                    difference
                )

                best_split = (
                    line1,
                    line2,
                )

    if best_split:

        return (
            f"{best_split[0]}\n"
            f"{best_split[1]}"
        )

    return text


# ============================================================
# Generate SRT
# ============================================================

def generate_srt(
    json_file,
    output_file,
    profile,
):

    with open(
        json_file,
        "r",
        encoding="utf-8",
    ) as f:

        data = json.load(f)

    timestamps = data["timestamps"]

    texts = (
        timestamps["words"]
    )

    starts = (
        timestamps[
            "start_time_seconds"
        ]
    )

    ends = (
        timestamps[
            "end_time_seconds"
        ]
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:

        caption_number = 1

        for text, start, end in zip(
            texts,
            starts,
            ends,
        ):

            # ----------------------------------------------
            # Normalize Saaras text
            # ----------------------------------------------

            text = normalize_caption_text(
                text
            )

            # ----------------------------------------------
            # Split caption
            # ----------------------------------------------

            captions = (
                split_caption_text(
                    text,
                    start,
                    end,
                    profile,
                )
            )

            # ----------------------------------------------
            # Write SRT entries
            # ----------------------------------------------

            for caption in captions:

                caption_text = (
                    format_caption(
                        caption["text"],
                        profile,
                    )
                )

                f.write(
                    f"{caption_number}\n"
                )

                f.write(
                    f"{srt_timestamp(caption['start'])}"
                    " --> "
                    f"{srt_timestamp(caption['end'])}"
                    "\n"
                )

                f.write(
                    caption_text
                    + "\n\n"
                )

                caption_number += 1


# ============================================================
# Get clean project/video name
# ============================================================

def get_base_name(json_path):

    name = json_path.name

    # Remove .json
    if name.lower().endswith(
        ".json"
    ):
        name = name[:-5]

    # Saaras gives files like:
    # day8_audio.mp3.json
    #
    # Remove audio extension too.

    media_extensions = [
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".flac",
        ".ogg",
        ".mp4",
    ]

    for extension in media_extensions:

        if name.lower().endswith(
            extension
        ):

            name = (
                name[
                    :-len(extension)
                ]
            )

            break

    return name


# ============================================================
# Arguments
# ============================================================

parser = argparse.ArgumentParser(
    description=(
        "Generate optimized SRT captions "
        "from Saaras JSON"
    )
)

parser.add_argument(
    "json_file",
    help="Saaras JSON transcription file",
)

parser.add_argument(
    "--lines",
    type=int,
    choices=[1, 2],
    help=(
        "Caption layout. "
        "1 = vertical, 2 = horizontal"
    ),
)

args = parser.parse_args()


json_file = Path(
    args.json_file
)

if not json_file.exists():

    raise FileNotFoundError(
        f"JSON file not found: "
        f"{json_file}"
    )


# ============================================================
# Ask user for caption layout
# ============================================================

if args.lines is None:

    print()
    print(
        "Choose caption layout:"
    )

    print()

    print(
        "1. One line  "
        "- Vertical video / Reels / Shorts"
    )

    print(
        "2. Two lines "
        "- Horizontal video / YouTube"
    )

    print()

    while True:

        choice = input(
            "Enter 1 or 2: "
        ).strip()

        if choice in (
            "1",
            "2",
        ):

            line_mode = int(
                choice
            )

            break

        print(
            "Please enter 1 or 2."
        )

else:

    line_mode = args.lines


profile = (
    CAPTION_PROFILES[
        line_mode
    ]
)


# ============================================================
# Output filename
# ============================================================

base_name = get_base_name(
    json_file
)

output_file = (
    json_file.parent
    / (
        f"{base_name}_"
        f"{profile['name']}.srt"
    )
)


# ============================================================
# Generate caption file
# ============================================================

print()
print(
    f"Mode: "
    f"{profile['description']}"
)

print(
    f"Max lines: "
    f"{profile['max_lines']}"
)

print(
    f"Max characters per line: "
    f"{profile['max_chars_per_line']}"
)

print()

generate_srt(
    json_file=json_file,
    output_file=output_file,
    profile=profile,
)


print(
    "=============================="
)

print(
    "Caption generation complete!"
)

print(
    "=============================="
)

print(
    f"SRT: {output_file}"
)
