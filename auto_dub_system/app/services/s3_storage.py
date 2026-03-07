"""
AWS S3 Storage Service
Handles uploading dubbed videos to S3 and generating presigned download URLs.
"""

import os
import logging

logger = logging.getLogger(__name__)


def _get_s3_client():
    """Create and return a boto3 S3 client using app settings."""
    try:
        import boto3
        from app.config import settings

        return boto3.client(
            "s3",
            region_name=settings.AWS_S3_REGION,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )
    except ImportError:
        raise RuntimeError("boto3 is not installed. Run: pip install boto3")


def upload_to_s3(local_path: str, s3_key: str) -> str:
    """
    Upload a local file to the configured S3 bucket.

    Args:
        local_path: Absolute path to the local file.
        s3_key:     Destination key inside the S3 bucket (e.g. 'dubbed/video.mp4').

    Returns:
        The s3_key on success.

    Raises:
        Exception on upload failure.
    """
    from app.config import settings

    if not os.path.exists(local_path):
        raise FileNotFoundError(f"File not found for S3 upload: {local_path}")

    if not settings.AWS_S3_BUCKET_NAME:
        raise ValueError("AWS_S3_BUCKET_NAME is not set in .env")

    client = _get_s3_client()
    bucket = settings.AWS_S3_BUCKET_NAME

    logger.info(f"Uploading {local_path} → s3://{bucket}/{s3_key}")
    client.upload_file(
        local_path,
        bucket,
        s3_key,
        ExtraArgs={"ContentType": "video/mp4"},
    )
    logger.info(f"✅ S3 upload complete: s3://{bucket}/{s3_key}")
    return s3_key


def generate_presigned_url(s3_key: str, expiry: int = 3600) -> str:
    """
    Generate a presigned download URL for an object in S3.

    Args:
        s3_key: Key of the object inside the S3 bucket.
        expiry: URL expiry time in seconds (default 1 hour).

    Returns:
        A presigned HTTPS URL string.
    """
    from app.config import settings

    if not settings.AWS_S3_BUCKET_NAME:
        raise ValueError("AWS_S3_BUCKET_NAME is not set in .env")

    client = _get_s3_client()
    bucket = settings.AWS_S3_BUCKET_NAME

    url = client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": bucket,
            "Key": s3_key,
            # Force browser to download (not stream) the file
            "ResponseContentDisposition": f'attachment; filename="{os.path.basename(s3_key)}"',
        },
        ExpiresIn=expiry,
    )
    logger.info(f"Generated presigned URL for {s3_key} (expires in {expiry}s)")
    return url
