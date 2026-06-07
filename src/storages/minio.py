import urllib3
from minio import Minio

from src.config import settings

http_client = urllib3.PoolManager(
    timeout=urllib3.Timeout(connect=3.0, read=10.0),
    retries=urllib3.Retry(
        total=2,
        backoff_factor=0.2,
        status_forcelist=[500, 502, 503, 504],
    ),
)

minio_client: Minio = Minio(
    endpoint=settings.minio.endpoint,
    secure=settings.minio.secure,
    region=settings.minio.region,
    access_key=settings.minio.access_key,
    secret_key=settings.minio.secret_key.get_secret_value(),
    http_client=http_client,
)
