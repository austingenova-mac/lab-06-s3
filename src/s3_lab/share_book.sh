#!/bin/bash
set -euo pipefail

# --- check arguments ---
if [ "$#" -lt 3 ]; then
    echo "Usage: $0 <gutenberg-book-url> <bucket-name> <expiration-seconds>" >&2
    echo "Example: $0 https://www.gutenberg.org/cache/epub/84/pg84.txt secret-mst3k 3600" >&2
    exit 1
fi

URL="$1"
BUCKET="$2"
EXPIRES="$3"

# file name is the last part of the URL, e.g. pg84.txt
FILENAME="$(basename "$URL")"
LOCAL_PATH="books/$FILENAME"

# --- download the book into books/ ---
mkdir -p books
echo "Downloading $URL to $LOCAL_PATH"
curl -fsSL "$URL" -o "$LOCAL_PATH"

# --- create the bucket unless it already exists ---
if aws s3 ls "s3://$BUCKET" > /dev/null 2>&1; then
    echo "Bucket $BUCKET already exists"
else
    echo "Creating bucket $BUCKET"
    aws s3 mb "s3://$BUCKET"
fi

# --- upload the book (bucket and object stay private) ---
echo "Uploading $LOCAL_PATH to s3://$BUCKET/$FILENAME"
aws s3 cp "$LOCAL_PATH" "s3://$BUCKET/$FILENAME" --content-type "text/plain; charset=utf-8"

# --- presign a temporary URL and print it ---
echo "Presigned URL (expires in $EXPIRES seconds):"
aws s3 presign "s3://$BUCKET/$FILENAME" --expires-in "$EXPIRES"