"""Generate optimized SRT captions from Saaras transcription JSON."""

import argparse
import json
import re
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
# Caption splitting configuration
# ============================================================

PREFERRED_BREAKS = {
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


MEDIA_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".m4a",
    ".aac",
    ".flac",
    ".ogg",
    ".mp4",
)


# ============================================================
# Text cleanup
# ============================================================

def normalize_caption_text(text):
    """Normalize common words and spacing in caption text."""

    # --------------------------------------------------------
    # "day eight" -> "day 8"
    # --------------------------------------------------------

    day_pattern = (
        r"\bday\s+("
        + "|".join(DAY_NUMBERS.keys())
        + r")\b"
    )

    def replace_day_number(match):
        """Replace a written day number with its numeric value."""

        number_word = match.group(1).lower()

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

    # --------------------------------------------------------
    # Remove duplicate spaces
    # --------------------------------------------------------

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
    """Convert seconds into an SRT timestamp."""

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
# Caption size helpers
# ============================================================

def caption_character_limit(profile):
    """Return the maximum total characters allowed in a caption."""

    return (
        profile["max_chars_per_line"]
        * profile["max_lines"]
    )


def calculate_target_words(
    text,
    words,
    duration,
    profile,
):
    """Calculate the approximate number of words per caption."""

    max_words = profile["max_words"]
    max_duration = profile["max_duration"]

    max_chars = caption_character_limit(
        profile
    )

    # --------------------------------------------------------
    # Number of chunks needed because of word count
    # --------------------------------------------------------

    chunks_by_words = max(
        1,
        (
            len(words)
            + max_words
            - 1
        )
        // max_words,
    )

    # --------------------------------------------------------
    # Number of chunks needed because of duration
    # --------------------------------------------------------

    chunks_by_duration = max(
        1,
        int(
            (
                duration
                + max_duration
                - 0.001
            )
            // max_duration
        ),
    )

    # --------------------------------------------------------
    # Number of chunks needed because of character count
    # --------------------------------------------------------

    chunks_by_characters = max(
        1,
        (
            len(text)
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

    return max(
        1,
        round(
            len(words)
            / number_of_chunks
        ),
    )


# ============================================================
# Word splitting helpers
# ============================================================

def is_natural_break(word):
    """Return True when a word is a good place to break captions."""

    punctuation_break = word.endswith(
        (
            ".",
            "?",
            "!",
            ",",
        )
    )

    cleaned_word = (
        word.lower()
        .strip(".,?!")
    )

    preferred_word_break = (
        cleaned_word
        in PREFERRED_BREAKS
    )

    return (
        punctuation_break
        or preferred_word_break
    )


def split_words_into_chunks(
    words,
    target_words,
    max_words,
    max_chars,
):
    """Split words into caption-sized chunks."""

    chunks = []
    current = []
    current_chars = 0

    for word in words:
        word_chars = len(word)

        projected_chars = (
            current_chars
            + (1 if current else 0)
            + word_chars
        )

        # ----------------------------------------------------
        # If adding the next word would make the caption
        # too wide, finish the previous caption.
        # ----------------------------------------------------

        if (
            current
            and projected_chars > max_chars
        ):
            chunks.append(current)

            current = []
            current_chars = 0

        # ----------------------------------------------------
        # Add word to current caption
        # ----------------------------------------------------

        current.append(word)

        if current_chars:
            current_chars += 1

        current_chars += word_chars

        # ----------------------------------------------------
        # Don't break before reaching our target size
        # ----------------------------------------------------

        if len(current) < target_words:
            continue

        # ----------------------------------------------------
        # Prefer natural breaks once target size is reached
        # ----------------------------------------------------

        should_break = (
            is_natural_break(word)
            or len(current) >= max_words
        )

        if should_break:
            chunks.append(current)

            current = []
            current_chars = 0

    # --------------------------------------------------------
    # Add any remaining words
    # --------------------------------------------------------

    if current:
        chunks.append(current)

    return chunks


# ============================================================
# Caption timestamp helpers
# ============================================================

def build_caption_blocks(
    chunks,
    start,
    end,
):
    """Assign approximate timestamps to caption chunks."""

    caption_blocks = []

    current_time = start

    words_remaining = sum(
        len(chunk)
        for chunk in chunks
    )

    time_remaining = (
        end - start
    )

    last_index = (
        len(chunks)
        - 1
    )

    for index, chunk in enumerate(
        chunks
    ):
        chunk_word_count = len(chunk)

        # ----------------------------------------------------
        # Last caption finishes exactly at Saaras timestamp
        # ----------------------------------------------------

        if index == last_index:
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

        current_time = chunk_end

    return caption_blocks


# ============================================================
# Smart caption splitter
# ============================================================

def split_caption_text(
    text,
    start,
    end,
    profile,
):
    """Split caption text according to profile limits and timing."""

    words = text.strip().split()

    if not words:
        return []

    duration = (
        end - start
    )

    target_words = calculate_target_words(
        text=text,
        words=words,
        duration=duration,
        profile=profile,
    )

    chunks = split_words_into_chunks(
        words=words,
        target_words=target_words,
        max_words=profile["max_words"],
        max_chars=caption_character_limit(
            profile
        ),
    )

    return build_caption_blocks(
        chunks=chunks,
        start=start,
        end=end,
    )


# ============================================================
# Caption line formatting
# ============================================================

def format_caption(
    text,
    profile,
):
    """Format caption text into one or two display lines."""

    max_lines = profile["max_lines"]

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

    for index in range(
        1,
        len(words),
    ):
        line_one = " ".join(
            words[:index]
        )

        line_two = " ".join(
            words[index:]
        )

        lines_fit = (
            len(line_one) <= max_chars
            and len(line_two) <= max_chars
        )

        if not lines_fit:
            continue

        difference = abs(
            len(line_one)
            - len(line_two)
        )

        if difference < best_difference:
            best_difference = difference

            best_split = (
                line_one,
                line_two,
            )

    if best_split:
        return (
            f"{best_split[0]}\n"
            f"{best_split[1]}"
        )

    return text


# ============================================================
# Saaras JSON helpers
# ============================================================

def load_timestamps(json_file):
    """Load timestamp information from a Saaras JSON file."""

    with open(
        json_file,
        "r",
        encoding="utf-8",
    ) as input_file:
        data = json.load(
            input_file
        )

    return data["timestamps"]


# ============================================================
# SRT writing helpers
# ============================================================

def write_srt_entry(
    output_handle,
    caption_number,
    caption,
    profile,
):
    """Write one caption block to an SRT file."""

    caption_text = format_caption(
        caption["text"],
        profile,
    )

    output_handle.write(
        f"{caption_number}\n"
    )

    output_handle.write(
        f"{srt_timestamp(caption['start'])}"
        " --> "
        f"{srt_timestamp(caption['end'])}"
        "\n"
    )

    output_handle.write(
        caption_text
        + "\n\n"
    )

    return (
        caption_number
        + 1
    )


# ============================================================
# Generate SRT
# ============================================================

def generate_srt(
    json_file,
    output_file,
    profile,
):
    """Generate an optimized SRT file from Saaras JSON."""

    timestamps = load_timestamps(
        json_file
    )

    caption_number = 1

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as output_handle:

        for text, start, end in zip(
            timestamps["words"],
            timestamps[
                "start_time_seconds"
            ],
            timestamps[
                "end_time_seconds"
            ],
        ):
            # ----------------------------------------------
            # Normalize Saaras text
            # ----------------------------------------------

            normalized_text = (
                normalize_caption_text(
                    text
                )
            )

            # ----------------------------------------------
            # Split caption
            # ----------------------------------------------

            captions = split_caption_text(
                normalized_text,
                start,
                end,
                profile,
            )

            # ----------------------------------------------
            # Write SRT entries
            # ----------------------------------------------

            for caption in captions:
                caption_number = (
                    write_srt_entry(
                        output_handle,
                        caption_number,
                        caption,
                        profile,
                    )
                )


# ============================================================
# Get clean project/video name
# ============================================================

def get_base_name(json_path):
    """Return a clean video name from a Saaras JSON filename."""

    name = json_path.name

    # --------------------------------------------------------
    # Remove .json
    # --------------------------------------------------------

    if name.lower().endswith(
        ".json"
    ):
        name = name[:-5]

    # --------------------------------------------------------
    # Saaras gives files such as:
    #
    # day8_audio.mp3.json
    #
    # Remove audio/video extension too.
    # --------------------------------------------------------

    for extension in MEDIA_EXTENSIONS:
        if name.lower().endswith(
            extension
        ):
            name = name[
                :-len(extension)
            ]

            break

    return name


# ============================================================
# Argument parser
# ============================================================

def build_argument_parser():
    """Create and return the command-line argument parser."""

    parser = argparse.ArgumentParser(
        description=(
            "Generate optimized SRT captions "
            "from Saaras JSON"
        )
    )

    parser.add_argument(
        "json_file",
        help=(
            "Saaras JSON transcription file"
        ),
    )

    parser.add_argument(
        "--lines",
        type=int,
        choices=[
            1,
            2,
        ],
        help=(
            "Caption layout. "
            "1 = vertical, "
            "2 = horizontal"
        ),
    )

    return parser


# ============================================================
# Caption layout selection
# ============================================================

def select_line_mode(
    requested_lines,
):
    """Return requested caption mode or ask the user interactively."""

    if requested_lines is not None:
        return requested_lines

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
            return int(
                choice
            )

        print(
            "Please enter 1 or 2."
        )


# ============================================================
# Profile information
# ============================================================

def display_profile(profile):
    """Display the selected caption profile."""

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


# ============================================================
# Completion message
# ============================================================

def display_completion(
    output_file,
):
    """Display the caption generation completion message."""

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


# ============================================================
# Main
# ============================================================

def main():
    """Run the caption generation command-line application."""

    parser = build_argument_parser()

    args = parser.parse_args()

    json_file = Path(
        args.json_file
    )

    if not json_file.exists():
        raise FileNotFoundError(
            f"JSON file not found: "
            f"{json_file}"
        )

    # --------------------------------------------------------
    # Select caption layout
    # --------------------------------------------------------

    line_mode = select_line_mode(
        args.lines
    )

    profile = (
        CAPTION_PROFILES[
            line_mode
        ]
    )

    # --------------------------------------------------------
    # Output filename
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Generate caption file
    # --------------------------------------------------------

    display_profile(
        profile
    )

    generate_srt(
        json_file=json_file,
        output_file=output_file,
        profile=profile,
    )

    display_completion(
        output_file
    )


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    main()
