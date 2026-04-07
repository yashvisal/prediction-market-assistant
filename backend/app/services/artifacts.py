from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

import boto3

from app.config import Settings
from app.services.persistence import ArtifactRecord


def _slug(value: str) -> str:
    return value.replace(":", "-").replace("/", "-").replace("\\", "-")


@dataclass(frozen=True)
class StoredArtifact:
    record: ArtifactRecord
    payload_bytes: bytes


class ArtifactStore:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._client = boto3.client(
            "s3",
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )

    def put_json(
        self,
        *,
        owner_type: str,
        owner_id: str,
        artifact_type: str,
        payload: Any,
        captured_at: datetime,
        source_url: str | None = None,
        parser_version: str = "v1",
        metadata: dict[str, Any] | None = None,
    ) -> StoredArtifact:
        payload_bytes = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        checksum = hashlib.sha256(payload_bytes).hexdigest()
        object_key = (
            f"{self._settings.s3_prefix.rstrip('/')}/{owner_type}/{_slug(owner_id)}/"
            f"{artifact_type}-{captured_at.strftime('%Y%m%dT%H%M%SZ')}-{checksum[:12]}.json"
        )
        self._client.put_object(
            Bucket=self._settings.s3_bucket,
            Key=object_key,
            Body=payload_bytes,
            ContentType="application/json",
        )
        record = ArtifactRecord(
            id=f"artifact-{uuid4()}",
            owner_type=owner_type,
            owner_id=owner_id,
            bucket=self._settings.s3_bucket,
            object_key=object_key,
            content_type="application/json",
            checksum=checksum,
            source_url=source_url,
            parser_version=parser_version,
            captured_at=captured_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
            metadata=metadata or {},
        )
        return StoredArtifact(record=record, payload_bytes=payload_bytes)
