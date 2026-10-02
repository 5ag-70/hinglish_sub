#!/bin/bash

set -euo pipefail

# ============================================================
# Check argument
# ============================================================

if [[ $# -lt 1 ]]; then
    echo "Usage: $0 <video-or-audio-file>"
    exit 1
fi

filename="$1"

# ============================================================
# Check input file
# ============================================================

if [[ ! -f "$filename" ]]; then
    echo "Error: File not found: $filename"
    exit 1
fi

# ============================================================
# Build output filename
# ============================================================

name="${filename##*/}"
output_file_name="${name%.*}"

output_file="${output_file_name}.wav"

# ============================================================
# Extract audio
# ============================================================

echo "Input : $filename"
echo "Output: $output_file"
echo

ffmpeg \
    -hide_banner \
    -i "$filename" \
    -map 0:a:0 \
    -vn \
    -ac 1 \
    -ar 16000 \
    -c:a pcm_s16le \
    "$output_file"

echo
echo "Audio extracted successfully:"
echo "$output_file"
