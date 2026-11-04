"""AWS S3 업로드(선택): S3_BUCKET이 있을 때만 수집 원본(JSON)과 주간 리포트(엑셀)를 보관한다.

인증은 boto3 기본 방식(EC2 IAM 역할 또는 AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY)을 따른다.
"""
import logging

log = logging.getLogger(__name__)


def upload(bucket: str, key: str, data: bytes, content_type: str, region: str | None = None) -> str | None:
    if not bucket:
        return None
    try:
        import boto3

        boto3.client("s3", region_name=region or None).put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
        return f"s3://{bucket}/{key}"
    except Exception as exc:  # 업로드 실패가 수집 자체를 막지 않게 한다
        log.warning("S3 업로드 실패 %s: %s", key, exc)
        return None
