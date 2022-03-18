import os
from datetime import datetime, timezone, timedelta

import boto3


def download_files_from_s3(local_path, s3_bucket=os.environ['S3_BUCKET'], s3_directory='', within_days=None):
    current = datetime.now(timezone.utc)
    if within_days is None:
        time_point = datetime.strptime('1970-01-01 00:00:00+00:00', "%Y-%m-%d %H:%M:%S%z")
    else:
        time_point = current - timedelta(days=within_days)

    if not os.path.exists(local_path):
        print('Making download directory "%s" ...' % local_path)
        os.makedirs(local_path)
    client = boto3.client('s3')

    paginator = client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=s3_bucket, Prefix=s3_directory):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                last_modified = obj['LastModified']
                if key[-1] == '/':
                    continue
                absolute_path = os.path.join(local_path, *(key.split('/')[1:-1]))
                if not os.path.exists(absolute_path):
                    os.makedirs(absolute_path)
                file_name = os.path.join(absolute_path, key.split('/')[-1])
                if os.path.isfile(file_name) and last_modified < time_point:
                    pass
                else:
                    client.download_file(Bucket=s3_bucket, Key=key, Filename=file_name)


def get_report():
    report_path = 'allure_reports'
    local_path = os.path.join(os.path.abspath(os.sep), 'var', report_path)
    days = None
    if os.path.exists(local_path):
        days = 0.1
    download_files_from_s3(local_path, s3_directory=os.path.join(report_path, '').replace('\\', '/'), within_days=days)


if __name__ == '__main__':
    get_report()
