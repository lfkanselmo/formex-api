from __future__ import annotations

import aioboto3


class S3DocumentStorage:
    def __init__(
        self,
        endpoint_url: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        region: str = "us-east-1",
    ) -> None:
        self._endpoint_url = endpoint_url
        self._access_key = access_key
        self._secret_key = secret_key
        self._bucket = bucket
        self._region = region
        self._session = aioboto3.Session()

    async def save(self, key: str, content: bytes) -> None:
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        ) as client:
            await client.put_object(Bucket=self._bucket, Key=key, Body=content)

    async def load(self, key: str) -> bytes:
        async with self._session.client(
            "s3",
            endpoint_url=self._endpoint_url,
            aws_access_key_id=self._access_key,
            aws_secret_access_key=self._secret_key,
            region_name=self._region,
        ) as client:
            response = await client.get_object(Bucket=self._bucket, Key=key)
            body: bytes = await response["Body"].read()
            return body
