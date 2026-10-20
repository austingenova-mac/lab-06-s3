## My S3 buckets
https://public-wwu7hk.s3.amazonaws.com/index.html
https://secret-wwu7hk.s3.amazonaws.com/pg87.txt?AWSAccessKeyId=ASIASNEGY7QZ6QXHLWW3&Signature=vo0HOmR9SAO7ckC3Ny3bg3dq1KE%3D&x-amz-security-token=IQoJb3JpZ2luX2VjEIL%2F%2F%2F%2F%2F%2F%2F%2F%2F%2FwEaCXVzLXdlc3QtMiJIMEYCIQCdGZav7%2BwlpLTQhiiurwg32SU%2Bo8Eil%2BSLjDo7NY26VgIhAIihFXwsjA3842LFINfTqFFWUYpK%2FK8nT%2BIrv%2FL%2Bv5ESKq0CCEsQABoMMTY1NjM4ODk2NjkxIgwuKSscTHuDixC%2BQiMqigK4a3twUFF%2BQgdem0weutpY11WuHk9x94%2BdkF19itInjTL8ScrdVBxevFHaAS3cmtYJ4Xs2SUZiXguc0EOGZ7b0mEVW5dfOz%2B%2BCzed1cr36zMbDNn%2BUAgRSR%2BaHoJlXFjmmThUeqdJ07Tyf7%2FMw8wc99GHTRLyna3j34AcUON%2BHK1HBlhgPM%2Bj4RM2iqHlXB1ThBkG%2FMdKMmXN78BTDIvYAT8ujA%2BXLujsnRQQoJCfnkSgCuYbO3AtiWZgsTTCaKnVznX7j3Qo%2FGPu8dCNE7NKg20rMe9uvfx0jalZGq5rp1%2BoV28YBcMQacDBUJyG5ezpXDL1qBq1chr1u5tc5S7PHxf6MrJBybzAHJzDx2d7WBjqcAWyeiV9obBYiSUTPoOLKEhoqwWFyK206hbdVB4dBYPMqzQ4o0moUWDzXXllqYCBwWVmii2g8%2FAfY3rGtdJOLb4zKmzKY2E%2Fd0GSAtIsuJcxqlQ1mRcMbQyif4OeEAMV%2FvQ%2FtvJ%2B2K5kGvt8nIVhlufaVsqEgXQaPdxo1pxjKnEFeQbSexTbhd5SuS%2FTYokr8jVe%2BoAM%2FMHWhjKaZQg%3D%3D&Expires=1793126138
In my opinion, you would want to use a public bucket when the information you are posting isnt sensitive, and you would use a private one when it is sensitive data but still needs to be accesed by other people!
# Lab 06: Working with S3 Storage

The goal of this lab is to get you comfortable with **Amazon S3** object storage, building on what you have learned about the command line, AWS accounts, and scripting. You will stage a collection of 100 books from [Project Gutenberg](https://www.gutenberg.org/) in a **public** bucket that anyone can browse in a web browser, and share a single book from a **private** bucket with a time-limited presigned URL.

> **Note:** Review and adhere to the [coding best practices](https://github.com/ksiller/DS2022/blob/main/best-practices.md) where applicable when developing your scripts. The Python script in Task 1 and the bash script in Task 2 should follow the same scripting practices you used in [Lab 03](https://github.com/ksiller/lab-03-scripting), [Lab 04](https://github.com/ksiller/lab-04-sql), and [Lab 05](https://github.com/ksiller/lab-05-nosql): a shebang, functions with docstrings, comments, logging, `try`/`except` around calls to external services (AWS and web downloads), and an `if __name__ == "__main__":` block in Python, and `set -euo pipefail`, quoted variables, and validated positional arguments in bash. **Never put your AWS credentials in a script or commit them to GitHub.**

## Learning goals

By completing this lab, you will be able to:

- Install the AWS CLI as a `uv` tool, and set up a `uv` project with `boto3`.
- Configure the AWS CLI with temporary AWS Academy Learner Lab credentials and verify your identity.
- Explain why S3 buckets and objects are private by default, and when to share them with a bucket policy or a presigned URL.
- Write a Python script with `boto3` that creates a bucket, uploads a collection of files, and makes the bucket publicly readable.
- Write a bash script with the AWS CLI that uploads a file to a private bucket and presigns a URL to it.
- Document where your data lives and how to access it in a `README.md`.

**This lab stages the core dataset for Labs 07–09, where you will build an end-to-end text analysis pipeline that runs on your own computer, in AWS, and on UVA's High Performance Computing (HPC) system. Keep your public bucket after you finish this lab.**

## Setup

This lab requires a working Python 3 environment with the AWS CLI tool and the `boto3` package installed, and an AWS Academy Learner Lab session with its temporary credentials configured. Steps 3 and 4 below are the same as in [Class 06: S3](https://github.com/ksiller/DS2022/blob/main/class/06-s3/README.md).

### 1. Fork and clone this repository

Fork this repository on GitHub (keep the default name): [https://github.com/ksiller/lab-06-s3](https://github.com/ksiller/lab-06-s3). Clone **your fork** to your own computer. Recommended location: `~/ds2022-fall-2026/lab-06-s3`.

```bash
mkdir -p ~/ds2022-fall-2026/
cd ~/ds2022-fall-2026/
git clone https://github.com/YOUR_USERNAME/lab-06-s3.git
```

Do all of your work in the `lab-06-s3` directory. Commit and push deliverables to your fork, then submit the URL of the fork (see [Submit your work](#submit-your-work)).

The repository contains two files you will use in Task 1:

- `book_urls.txt`: the download URLs of 100 plain-text books from Project Gutenberg, one URL per line.
- `index.html`: a web page that lists the 100 books and links to each file. You will upload it to your public bucket.

### 2. Environment with AWS CLI and Python `boto3`

This lab uses a `uv` project, as in Lab 03, Lab 04, and Lab 05. Confirm that `uv` is installed (`uv --version`). If that command fails, install it by following [Installing uv](https://docs.astral.sh/uv/getting-started/installation/).

From the top-level directory of your clone, create the project:

```bash
cd ~/ds2022-fall-2026/lab-06-s3
uv init --name "s3_lab" --description "S3 work for DS2022"
```

We need three packages, installed in two different ways:

- `awscli`: provides the AWS CLI tools
- `boto3`: package to connect to AWS in your Python scripts
- `requests`: package to download the books in your Python script

The AWS CLI is a command line tool, not a library your scripts import, so install it as a `uv` tool. That makes the `aws` command available in every terminal, independent of any project environment. If you already installed it in class, you can skip this step:

```bash
uv tool install awscli
```

`boto3` and `requests` are imported by your Python script, so add them to the project:

```bash
uv add boto3 requests
```

Confirm with:

```bash
aws --version
uv tree
uv run python -c "import boto3, requests"
```

If you don't receive an error message, the AWS CLI and both packages are installed. If the shell reports `aws: command not found`, run `uv tool update-shell`, then open a new terminal so the `uv` tool directory is on your `PATH`.

- `uv init` creates `pyproject.toml`, `.python-version`, and a package directory `src/s3_lab/` (with `__init__.py`).
- `uv tool install awscli` installs the AWS CLI into its own isolated environment outside your repository. It is not recorded in `pyproject.toml`.
- `uv add boto3 requests` records both packages in `pyproject.toml`, writes `uv.lock` with exact versions, and installs them into `.venv/`. Do not edit `uv.lock` by hand.

This repository already includes a `.gitignore` that excludes `.venv/`, `.vscode/`, secret files such as `.env`, and the `books/` folder your scripts download into. Review that file, and leave those lines in place. On another computer, `uv sync` recreates the environment, including `.venv`, from `pyproject.toml` and `uv.lock`.

### 3. Start the AWS Academy Learner Lab

You work in your own **AWS Academy Learner Lab** account, as in [Class 06: S3](https://github.com/ksiller/DS2022/blob/main/class/06-s3/README.md#start-the-aws-academy-learner-lab).

1. Log in to **AWS Academy**, click **Start LMS**, and open the **Learner Lab** course.
2. Go to **Modules** and click **Launch AWS Academy Learner Lab**.
3. Click **Start Lab** and wait until the **AWS** icon in the top left corner turns green.
4. To open the AWS Management Console, click the **AWS** icon. The console opens in a new tab.

> **Do not click Reset.** Reset deletes everything in your lab account, including the public bucket you need for Labs 07–09. When a session ends (after about 4 hours, or when you click **End Lab**), your buckets stay in the account and are there again the next time you click **Start Lab**.

### 4. AWS CLI configuration (temporary credentials)

The Learner Lab has no long-lived access keys. Instead, each lab session provides temporary credentials (access key, secret key, and session token) for the `voclabs` role. Follow the [AWS CLI configuration](https://github.com/ksiller/DS2022/blob/main/class/06-s3/README.md#aws-cli-configuration-temporary-credentials) steps from class:

1. On the Learner Lab page, click **AWS Details**, then **Show** next to **AWS CLI**.
2. Copy the whole block, from `[default]` through the end of the long `aws_session_token` line.
3. Paste it into `~/.aws/credentials`, replacing anything already in the file, and save. It should look like this, with each value on a single line:

    ```text
    [default]
    aws_access_key_id=ASIA...
    aws_secret_access_key=...
    aws_session_token=...
    ```

4. Set the default region and output format (this writes `~/.aws/config`):

    ```bash
    aws configure set region us-east-1
    aws configure set output json
    ```

> **Credentials expire when the lab session ends (about 4 hours).** When `aws` or `boto3` suddenly fail with expired-token errors, click **Start Lab** again if the session has ended, open **AWS Details** → **AWS CLI** → **Show**, and replace the contents of `~/.aws/credentials` with the new block. Your buckets are not affected.

> **Note:** Remember, the creation of personal config files in hidden directories inside your home directory is a best-practice pattern. Because `~/.aws` lives outside your repository, your credentials are never tracked by Git.

**Verify**

```bash
cat ~/.aws/config
aws sts get-caller-identity
```

`get-caller-identity` should succeed and print something like this (your numbers and name will differ):

```json
{
    "UserId": "AROAZHRIMGJHAXBS5BBDQ:user5560460=Test_Student",
    "Account": "634666103374",
    "Arn": "arn:aws:sts::634666103374:assumed-role/voclabs/user5560460=Test_Student"
}
```

`assumed-role/voclabs/...` means you are working as the `voclabs` role in your Learner Lab account, not as an IAM user.

## Public and private buckets

S3 buckets are **private** by default: nothing you upload to a new bucket is accessible without credentials. In this lab you will share data in two different ways:

| Bucket | Who can read it | How |
| --- | --- | --- |
| `public-mst3k` (Task 1) | Anyone with the URL | Block Public Access turned off, plus a **bucket policy** that allows `s3:GetObject` for everyone |
| `secret-mst3k` (Task 2) | Only you, plus anyone you give a presigned URL to, until it expires | Default private settings, plus a **presigned URL** |

The web URL of an object in a bucket in `us-east-1` has this form:

```text
https://BUCKET_NAME.s3.amazonaws.com/KEY
```

For example, this URL points to a public file in the course bucket: [https://ds2022-fall26.s3.amazonaws.com/cloud.jpg](https://ds2022-fall26.s3.amazonaws.com/cloud.jpg)

> **Note:** Replace `mst3k` in all bucket names in this lab with your actual computing ID (in the shell, `$USER` expands to it). Bucket names must be **globally unique** across all of AWS (your own Learner Lab account does not give you a private name space). If a name is already taken, add a number, e.g. `public-mst3k-1`, and use that name throughout this lab and in Labs 07–09.

## Task 1: Stage books in a public bucket (Python)

**The Case:** A digital humanities group wants to analyze a corpus of classic books. Downloading the same 100 books from Project Gutenberg every time someone runs an analysis is slow and puts unnecessary load on Gutenberg's servers. You will stage the corpus once in S3, where any analysis (including yours in Labs 07–09) can read it, and publish a simple web page so collaborators can browse the collection.

**Your Task:** Write a Python script that downloads the books listed in `book_urls.txt`, creates a public bucket, uploads the books and `index.html` to it, and makes the bucket publicly readable.

### Step 1: Write the script

Create `stage_books.py` in `src/s3_lab/` (the package directory created by `uv init --name "s3_lab"`).

**Start from the class examples.** Read through the numbered scripts in [class/06-s3](https://github.com/ksiller/DS2022/tree/main/class/06-s3), in particular [`01-make-bucket.py`](https://github.com/ksiller/DS2022/blob/main/class/06-s3/01-make-bucket.py) (create a bucket in `us-east-1`) and [`04-upload-object.py`](https://github.com/ksiller/DS2022/blob/main/class/06-s3/04-upload-object.py) (upload a file with a content type). They show the logger setup, the S3 client, and `try`/`except` blocks with `botocore.exceptions.ClientError` that you should reuse. Do not copy the client from `03-download-object.py`: it is an anonymous client that can only read public objects, so every upload would fail.

Each class script performs a single step. Your script combines these steps into functions, structured as in Labs 03–05 (shebang, docstrings, comments, and a `main()` function called from an `if __name__ == "__main__":` block). The script should:

- Accept three command line arguments, in this order: the path of the book list file (`book_urls.txt`), the path of the index page (`index.html`), and the name of the bucket (`public-mst3k`).
- Set up the logger as in the class scripts, and use it to report status in each function.
- Create **one** S3 client at the top of the script, right after the logger, so that all functions share it. The class scripts create the client inside their `try` block; in your script, create it once at module level instead of in every function:

    ```python
    s3 = boto3.client("s3", region_name="us-east-1")
    ```

- Wrap calls to external services (HTTP downloads with `requests` and `boto3` calls to AWS) in `try`/`except` blocks that log the error.
- Define the functions below. For each one, the signature shows its arguments, followed by what it returns and what should happen inside.
  - `parse_args()`
    - **Arguments:** none; it reads the command line.
    - **Returns:** a tuple `(list_file, index_path, bucket)` of three strings.
    - **Inside:** read the three arguments from `sys.argv` (`sys.argv[1]`, `sys.argv[2]`, `sys.argv[3]`). If fewer than three are given, log a usage message and `sys.exit(1)`. *Optional:* use [`argparse`](https://docs.python.org/3/library/argparse.html) instead, which generates the usage message and `--help` text for you.
  - `download_books(list_file, dest_dir)`
    - **Arguments:** `list_file`, the path of the book list (`book_urls.txt`); `dest_dir`, the folder to save the books in (use `"books"`).
    - **Returns:** a list of the local paths of the books, e.g. `["books/pg11.txt", "books/pg12.txt", ...]`. You pass this list to `upload_files`.
    - **Inside:** create `dest_dir` with `os.makedirs(dest_dir, exist_ok=True)` (like `mkdir -p`). Read `list_file` (one URL per line, skip blank lines). For each URL, download the book with `requests` and save it in `dest_dir` under the last part of the URL. For example,

        ```text
        https://www.gutenberg.org/cache/epub/1342/pg1342.txt
        ```

        is saved as `books/pg1342.txt`. Keep these names, because the links in `index.html` point to them (`<a href="pg1342.txt">`). If the file already exists (check with `os.path.exists(path)`), skip the download, so you can rerun the script without downloading everything again. Pause for about a second between downloads (`time.sleep(1)`) to avoid bombarding Project Gutenberg's servers with requests. If a download fails, log the error and continue with the next book. **Hint:** inside the loop over the URLs, wrap the download in a `try`/`except` block. `requests.get()` raises an exception for network errors and timeouts, and `response.raise_for_status()` raises one for HTTP errors such as 404. `requests.RequestException` catches all of them.

        ```python
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()  # raise an error for 404 etc.
            # save response.content to the file
        except requests.RequestException as e:
            log.error(f"Error downloading {url}: {e}")
        ```

  - `create_bucket(bucket)`
    - **Arguments:** `bucket`, the bucket name.
    - **Returns:** `True` if the bucket exists afterwards, `False` otherwise.
    - **Inside:** first check whether the bucket already exists, for example from a previous run: `s3.head_bucket(Bucket=bucket)` succeeds if the bucket exists and you can access it, and raises a `ClientError` otherwise (the same idea as the `aws s3 ls` check in Task 2). If it exists, return `True`. Otherwise, create the bucket as in `01-make-bucket.py`. Creating a bucket that you already own raises an error, so do not skip the check.
  - `make_public(bucket)`
    - **Arguments:** `bucket`, the bucket name.
    - **Returns:** `True` on success, `False` otherwise.
    - **Inside:** turn off Block Public Access for the bucket, then attach a bucket policy that allows anyone to read its objects (see the hints below).
  - `upload_files(bucket, file_paths)`
    - **Arguments:** `bucket`, the bucket name; `file_paths`, the list returned by `download_books`.
    - **Returns:** the number of files uploaded successfully.
    - **Inside:** loop over `file_paths` and upload each file to the top level of the bucket, using the file name as the key (e.g. `pg1342.txt`, not `books/pg1342.txt`) and `ContentType="text/plain; charset=utf-8"`, so browsers display the books as text. If an upload fails, log the error and continue with the next file.
  - `upload_index(bucket, index_path)`
    - **Arguments:** `bucket`, the bucket name; `index_path`, the path of the index page from the command line.
    - **Returns:** `True` on success, `False` otherwise.
    - **Inside:** upload the file with the key `index.html` and `ContentType="text/html"`, so browsers display it as a web page. Handle a missing file as in `04-upload-object.py`.
  - `main()`
    - **Arguments:** none.
    - **Returns:** nothing.
    - **Inside:** call the functions above in order. Stop with `sys.exit(1)` if no books were downloaded or the bucket could not be created or made public. At the end, log a success or failure message and the public URL of the index page, `https://BUCKET.s3.amazonaws.com/index.html`.

**Hints:** The class scripts do not cover making a bucket public. Use these two calls in `make_public`.

- To turn off Block Public Access for one bucket:

    ```python
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )
    ```

- A bucket policy is a JSON document like this:

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Effect": "Allow",
          "Principal": "*",
          "Action": "s3:GetObject",
          "Resource": "arn:aws:s3:::public-mst3k/*"
        }
      ]
    }
    ```

    Build the policy as a Python dictionary named `policy`, and replace `public-mst3k` in the example with your `bucket` value. Then pass the dictionary as a string with `json.dumps(policy)` to `s3.put_bucket_policy()`:

    ```python
    s3.put_bucket_policy(Bucket=bucket, Policy=json.dumps(policy))
    ```

    The policy must be attached **after** Block Public Access is turned off, otherwise S3 rejects it with an `AccessDenied` error.

### Step 2: Run the script

Run the script from the top-level directory of your clone, replacing `mst3k` with your computing ID:

```bash
uv run python src/s3_lab/stage_books.py book_urls.txt index.html public-mst3k
```

Downloading 100 books takes a few minutes. Watch the log output for errors. If the script fails partway, fix the problem and rerun it: books that were already downloaded are skipped.

### Step 3: Verify

1. Count the books in your bucket. The total should be 101 objects (100 books plus `index.html`):

    ```bash
    aws s3 ls s3://public-mst3k/ | wc -l
    ```

2. Open `https://public-mst3k.s3.amazonaws.com/index.html` in your web browser, **in a private/incognito window** so that you are not signed in to AWS. You should see the list of books. Click a few links; each book should open as plain text.

3. Open the AWS Management Console (click the green **AWS** icon on the Learner Lab page), go to **S3**, and click `public-mst3k`. On the **Permissions** tab, confirm that Block Public Access is off and that your bucket policy is attached. The bucket should be labeled **Publicly accessible**.

**Success:** Anyone with the URL can now browse and read your book collection. Keep this bucket: Labs 07–09 read the books from it.

## Task 2: Share one book from a private bucket (bash)

**The Case:** Not all data should be public. A collaborator needs temporary access to a single book that should not be published, and they don't have an AWS account. A presigned URL grants read access to one object for a limited time, without changing the bucket's private settings.

**Your Task:** Write a bash script that downloads one book of your choice, uploads it to a new private bucket, and prints a presigned URL to it.

### Step 1: Write the script

In the top-level directory of your clone, create `share_book.sh`. The script should:

- Start with a shebang and strict error handling:

    ```bash
    #!/bin/bash
    set -euo pipefail
    ```

- Accept three positional arguments: the URL of a plain-text book on Project Gutenberg, the name of the bucket (`secret-mst3k`), and the expiration of the presigned URL in seconds. Print a usage message and `exit 1` if any argument is missing.
- Download the book with `curl` into the `books/` folder, keeping the file name from the URL.
- Create the bucket with `aws s3 mb`, unless it already exists. **Hint:** `aws s3 ls "s3://$BUCKET" > /dev/null 2>&1` succeeds only if the bucket exists and you can access it.
- Upload the book with `aws s3 cp`, setting `--content-type "text/plain; charset=utf-8"` so it displays in the browser. Do **not** change any public access settings: the bucket and the book stay private.
- Presign a URL to the book with `aws s3 presign` and the expiration from the third argument, and print it.
- Quote all variable expansions and add short comments for each step.

### Step 2: Pick a book

To pick a book, search [Project Gutenberg](https://www.gutenberg.org/), open the book's page, and copy the link of **Plain Text UTF-8**. It has the form `https://www.gutenberg.org/cache/epub/NUMBER/pgNUMBER.txt`. Choose a book that is not in `book_urls.txt`.

### Step 3: Run the script

Make the script executable and run it, replacing `NUMBER` and `mst3k`:

```bash
chmod +x share_book.sh
./share_book.sh https://www.gutenberg.org/cache/epub/NUMBER/pgNUMBER.txt secret-mst3k 604800
```

`604800` seconds is 7 days.

> **Presigned URLs and temporary credentials:** A presigned URL is signed with the credentials that created it. Your Learner Lab credentials expire when the lab session ends (about 4 hours), and the URL **stops working at that point**, even if you set a longer expiration. In a production account with long-lived credentials, the URL would stay valid for the full 7 days.

### Step 4: Verify

1. Open `https://secret-mst3k.s3.amazonaws.com/pgNUMBER.txt` in your browser. You should see an `AccessDenied` error: the book is private.
2. Open the presigned URL printed by your script. You should see the text of the book.
3. Run the script again with an expiration of `30` seconds. Open the new URL right away, then refresh the page after 30 seconds. What do you see?

**Success:** You've shared a private object without making it public, and seen how presigned URLs expire.

## Task 3: Document your buckets

Add a section `## My S3 buckets` at the **top** of this `README.md` (above the `# Lab 06` title), so that it is the first thing a visitor sees on your fork's GitHub page. It should include:

- A link to the index page of your public bucket, e.g. `https://public-mst3k.s3.amazonaws.com/index.html`.
- A link to the book in your secret bucket, presigned with an expiration of `604800` seconds. Run `share_book.sh` again right before you submit, so the link is as fresh as possible.
- One or two sentences on when you would choose a public bucket and when a presigned URL.

Because of the Learner Lab session limit, the presigned link will stop working within a few hours. That is expected; graders check that it has the right form and that `share_book.sh` produces it.

## Limitations of this approach

Your public collection works, but it has shortcomings you will address in later labs:

- `index.html` is a static file. Books you add to the bucket later do not appear on the page until you update and re-upload it.
- The web page is bare-bones, with no formatting.
- The page shows no information about each book beyond its title and file name.

## Submit your work

Your repository should look roughly like this (other `uv init` files are fine too):

```text
lab-06-s3/
├── .gitignore
├── .python-version
├── README.md
├── book_urls.txt
├── index.html
├── share_book.sh
├── pyproject.toml
├── uv.lock
└── src/
    └── s3_lab/
        ├── __init__.py
        └── stage_books.py
```

- `stage_books.py` (Task 1) downloads the books, creates your public bucket, makes it public, and uploads the books and `index.html`.
- `share_book.sh` (Task 2) downloads one book, uploads it to your private bucket, and presigns a URL to it.
- `README.md` (Task 3) starts with links to your public index page and your presigned book.

The downloaded books in `books/` are listed in `.gitignore`. They are generated files and stay out of your repository; your bucket is now the place where they are stored.

**Submission steps**

Confirm that `.venv`, `.vscode`, and `books/` are listed in `.gitignore`, then run `git status` and verify that `.venv/`, `.vscode/`, and `books/` are **not** staged for commit. Double-check that none of your files contain your AWS credentials.

Add all project files (gitignored paths stay out automatically):

```bash
git add .
```

Commit your work:

```bash
git commit -m "Complete Lab 06: Working with S3 Storage"
```

Push to your repository:

```bash
git push origin main
```

Submit the URL of your forked repository in the Canvas assignment. The URL should look like: `https://github.com/YOUR_USERNAME/lab-06-s3`

> **Keep your buckets.** Do not delete `public-mst3k`; Labs 07–09 read the books from it. Do not click **Reset** in the Learner Lab.
