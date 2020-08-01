import datetime
import gzip
import io

import boto3
import tqdm


def upload_hook(t):
    def inner(bytes_amount):
        t.update(bytes_amount)

    return inner


def upload():
    s3 = boto3.client("s3")

    dbs = {
        "db.sqlite3": "all-data.sqlite3.gz",
        "frontend.sqlite3": "frontend.sqlite3.gz",
    }

    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%SZ")

    print("Saving files to s3")

    for disk_name, s3_name in dbs.items():
        object_name = f"v3/{timestamp}-{s3_name}"

        with open(disk_name, "rb") as file:
            compressed_file = gzip.compress(file.read())
            compressed_size = len(compressed_file)

            with tqdm.tqdm(
                total=compressed_size, unit="B", unit_scale=True, desc=disk_name
            ) as t:
                s3.upload_fileobj(
                    io.BytesIO(compressed_file),
                    "kijiji-apartments",
                    object_name,
                    Callback=upload_hook(t),
                )

    print("...done")
