import json
import logging
import os
import sys
import time

import boto3
import requests
from botocore.exceptions import ClientError

# --- logger setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

# --- one shared S3 client for all functions ---
s3 = boto3.client("s3", region_name="us-east-1")


def parse_args():
    """Read the book list path, index page path, and bucket name from the command line.

    Returns:
        tuple: (list_file, index_path, bucket) as strings.
    """
    if len(sys.argv) < 4:
        log.error("Usage: python stage_books.py <book_urls.txt> <index.html> <bucket-name>")
        sys.exit(1)

    list_file, index_path, bucket = sys.argv[1], sys.argv[2], sys.argv[3]
    log.info(f"Book list: {list_file}, index page: {index_path}, bucket: {bucket}")
    return list_file, index_path, bucket


def download_books(list_file, dest_dir):
    """Download each book URL in list_file into dest_dir.

    Skips books that already exist locally and pauses between downloads
    to avoid overloading Project Gutenberg.

    Args:
        list_file (str): Path to a file with one URL per line.
        dest_dir (str): Folder to save the books in.

    Returns:
        list: Local paths of the books that are available (downloaded or already present).
    """
    os.makedirs(dest_dir, exist_ok=True)

    try:
        with open(list_file) as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        log.error(f"Book list not found: {list_file}")
        return []

    log.info(f"Found {len(urls)} book URLs in {list_file}")
    paths = []

    for url in urls:
        filename = url.rstrip("/").split("/")[-1]  # e.g. pg1342.txt
        path = os.path.join(dest_dir, filename)

        # skip books we already have from a previous run
        if os.path.exists(path):
            log.info(f"Already have {path}, skipping download")
            paths.append(path)
            continue

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # raise an error for 404 etc.
            with open(path, "wb") as out:
                out.write(response.content)
            log.info(f"Downloaded {url} -> {path}")
            paths.append(path)
        except requests.RequestException as e:
            log.error(f"Error downloading {url}: {e}")

        time.sleep(1)  # be polite to Gutenberg's servers

    log.info(f"{len(paths)} of {len(urls)} books available locally")
    return paths


def create_bucket(bucket):
    """Create the bucket in us-east-1 unless it already exists.

    Args:
        bucket (str): Bucket name.

    Returns:
        bool: True if the bucket exists afterwards, False otherwise.
    """
    # check whether the bucket already exists (e.g. from a previous run)
    try:
        s3.head_bucket(Bucket=bucket)
        log.info(f"Bucket {bucket} already exists")
        return True
    except ClientError:
        log.info(f"Bucket {bucket} not found, creating it")

    try:
        # us-east-1 needs no CreateBucketConfiguration
        s3.create_bucket(Bucket=bucket)
        log.info(f"Created bucket {bucket}")
        return True
    except ClientError as e:
        log.error(f"Error creating bucket {bucket}: {e}")
        return False


def make_public(bucket):
    """Turn off Block Public Access and attach a public-read bucket policy.

    Args:
        bucket (str): Bucket name.

    Returns:
        bool: True on success, False otherwise.
    """
    # Block Public Access must be off before the policy can be attached
    try:
        s3.put_public_access_block(
            Bucket=bucket,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": False,
                "IgnorePublicAcls": False,
                "BlockPublicPolicy": False,
                "RestrictPublicBuckets": False,
            },
        )
        log.info(f"Turned off Block Public Access for {bucket}")
    except ClientError as e:
        log.error(f"Error turning off Block Public Access for {bucket}: {e}")
        return False

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket}/*",
            }
        ],
    }

    try:
        s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
        log.info(f"Attached public-read policy to {bucket}")
        return True
    except ClientError as e:
        log.error(f"Error attaching bucket policy to {bucket}: {e}")
        return False


def upload_files(bucket, file_paths):
    """Upload each book to the top level of the bucket as plain text.

    Args:
        bucket (str): Bucket name.
        file_paths (list): Local paths returned by download_books.

    Returns:
        int: Number of files uploaded successfully.
    """
    uploaded = 0

    for path in file_paths:
        key = os.path.basename(path)  # pg1342.txt, not books/pg1342.txt
        try:
            s3.upload_file(
                path,
                bucket,
                key,
                ExtraArgs={"ContentType": "text/plain; charset=utf-8"},
            )
            log.info(f"Uploaded {path} -> s3://{bucket}/{key}")
            uploaded += 1
        except FileNotFoundError:
            log.error(f"File not found: {path}")
        except ClientError as e:
            log.error(f"Error uploading {path}: {e}")

    log.info(f"Uploaded {uploaded} of {len(file_paths)} books")
    return uploaded


def upload_index(bucket, index_path):
    """Upload the index page as index.html so browsers render it.

    Args:
        bucket (str): Bucket name.
        index_path (str): Local path of the index page.

    Returns:
        bool: True on success, False otherwise.
    """
    try:
        s3.upload_file(
            index_path,
            bucket,
            "index.html",
            ExtraArgs={"ContentType": "text/html"},
        )
        log.info(f"Uploaded {index_path} -> s3://{bucket}/index.html")
        return True
    except FileNotFoundError:
        log.error(f"Index page not found: {index_path}")
        return False
    except ClientError as e:
        log.error(f"Error uploading index page: {e}")
        return False


def main():
    """Download the books, stage them in a public bucket, and publish the index page."""
    list_file, index_path, bucket = parse_args()

    book_paths = download_books(list_file, "books")
    if not book_paths:
        log.error("No books were downloaded, stopping")
        sys.exit(1)

    if not create_bucket(bucket):
        log.error("Bucket could not be created, stopping")
        sys.exit(1)

    if not make_public(bucket):
        log.error("Bucket could not be made public, stopping")
        sys.exit(1)

    uploaded = upload_files(bucket, book_paths)
    index_ok = upload_index(bucket, index_path)

    url = f"https://{bucket}.s3.amazonaws.com/index.html"
    if uploaded == len(book_paths) and index_ok:
        log.info(f"Success: {uploaded} books and index page staged. Browse at {url}")
    else:
        log.warning(
            f"Finished with errors: {uploaded}/{len(book_paths)} books uploaded, "
            f"index page {'uploaded' if index_ok else 'failed'}. URL: {url}"
        )


if __name__ == "__main__":
    main()