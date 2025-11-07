from minio import Minio
from app.core.config import get_settings

settings = get_settings()

_client = Minio(
    settings.s3_endpoint.replace("http://","").replace("https://",""),
    access_key=settings.s3_access_key,
    secret_key=settings.s3_secret_key,
    secure=settings.s3_endpoint.startswith("https")
)

def upload_file(file_bytes: bytes, filename: str, content_type: str = "application/octet-stream") -> str:
    from io import BytesIO
    _client.put_object(
        bucket_name=settings.s3_bucket,
        object_name=filename,
        data=BytesIO(file_bytes),
        length=len(file_bytes),
        content_type=content_type,
    )
    return f"{settings.s3_endpoint}/{settings.s3_bucket}/{filename}"
