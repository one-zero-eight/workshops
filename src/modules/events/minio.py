import io
from urllib.parse import urlunsplit

from src.config import settings
from src.storages.minio import minio_client


def get_event_image_object_name(logo_file_id: str):
    return f"{settings.minio.event_images_prefix}{logo_file_id}"


def get_event_picture_url(logo_file_id: str):
    object_name = get_event_image_object_name(logo_file_id)
    # Build public URL
    return urlunsplit(
        minio_client._base_url.build(
            method="GET",
            region=minio_client._get_region(settings.minio.bucket),
            bucket_name=settings.minio.bucket,
            object_name=object_name,
        )
    )


def put_event_picture(logo_file_id: str, data: bytes, content_type: str):
    object_name = get_event_image_object_name(logo_file_id)
    minio_client.put_object(
        bucket_name=settings.minio.bucket,
        object_name=object_name,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def delete_event_picture(logo_file_id: str):
    object_name = get_event_image_object_name(logo_file_id)
    minio_client.remove_object(
        bucket_name=settings.minio.bucket,
        object_name=object_name,
    )
