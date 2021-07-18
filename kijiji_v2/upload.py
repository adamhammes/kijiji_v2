import datetime
import os
import subprocess

import boto3
import tqdm


def upload_hook(t):
    def inner(bytes_amount):
        t.update(bytes_amount)

    return inner


def upload(disable_progress=False):
    s3 = boto3.client("s3")

    dbs = {
        "db.sqlite3": "all-data.sqlite3.gz",
        "frontend.sqlite3": "frontend.sqlite3.gz",
    }

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    print("Saving files to s3")

    for disk_name, s3_name in dbs.items():
        subprocess.run(["gzip", disk_name], check=True)

        gzipped_name = disk_name + ".gz"
        object_name = f"v3/{timestamp}-{s3_name}"
        compressed_size = os.path.getsize(gzipped_name)

        with tqdm.tqdm(
            total=compressed_size,
            unit="B",
            unit_scale=True,
            desc=disk_name,
            disable=disable_progress,
        ) as t:
            s3.upload_file(
                gzipped_name, "kijiji-apartments", object_name, Callback=upload_hook(t),
            )

        os.remove(gzipped_name)

    print("...done")
