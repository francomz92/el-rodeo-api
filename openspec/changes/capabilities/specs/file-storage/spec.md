# File Storage Specification

## Purpose

S3-compatible file storage capability for the API. Provides upload, download, delete, and pre-signed URL generation for domain use cases (animal images, etc.). Follows the same port/adapter pattern as `ICacheService`.

## Requirements

### Requirement: IFileStorageService port

The system MUST define an `IFileStorageService` ABC with four abstract methods:

- `upload(file: bytes, key: str, content_type: str) -> str` — uploads bytes to S3 under `key`, returns the pre-signed URL.
- `download(key: str) -> bytes` — retrieves file bytes for `key`.
- `delete(key: str) -> None` — removes the object at `key`; no-op if missing.
- `get_url(key: str) -> str` — returns a pre-signed GET URL with 1-hour expiry.

#### Scenario: Upload succeeds and returns URL

- GIVEN bytes `b"image-data"`, key `"animals/t1/abc/def.jpg"`, and content-type `"image/jpeg"`
- WHEN `IFileStorageService.upload()` is called
- THEN it returns a string starting with `https://` and the object exists at the given key

#### Scenario: Download retrieves stored bytes

- GIVEN an object stored at key `"animals/t1/abc/def.jpg"`
- WHEN `IFileStorageService.download(key)` is called
- THEN the returned bytes equal the originally uploaded bytes

#### Scenario: Delete removes object

- GIVEN an object exists at key `"animals/t1/abc/def.jpg"`
- WHEN `IFileStorageService.delete(key)` is called
- THEN subsequent `download(key)` raises a not-found error

#### Scenario: Get URL returns expiring pre-signed URL

- GIVEN an object exists at key `"animals/t1/abc/def.jpg"`
- WHEN `IFileStorageService.get_url(key)` is called
- THEN it returns a URL containing `"X-Amz-Signature"` and `"X-Amz-Expires=3600"`

### Requirement: S3FileStorageService adapter

The system MUST provide an `S3FileStorageService(IFileStorageService)` implementation that wraps sync `boto3` calls via `asyncio.to_thread()`. The adapter SHALL use the configured bucket, region, and endpoint from settings. It MUST prefix all keys with a configurable prefix (default `"el-rodeo/"`).

#### Scenario: Key prefix prepended to all operations

- GIVEN an `S3FileStorageService` with `key_prefix="el-rodeo/"`
- WHEN `upload(b"data", "animals/img.jpg", "image/jpeg")` is called
- THEN the S3 `put_object` receives key `"el-rodeo/animals/img.jpg"`

#### Scenario: Upload failure propagates as S3FileStorageError

- GIVEN the S3 client raises `ClientError` on `put_object`
- WHEN `upload()` is called
- THEN the adapter raises `S3FileStorageError` with the original cause

### Requirement: S3 settings in Settings

The system MUST add these env vars to `Settings` in `_config.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `S3_BUCKET` | — | S3 bucket name |
| `S3_REGION` | `"us-east-1"` | AWS region |
| `S3_ACCESS_KEY` | — | AWS access key ID |
| `S3_SECRET_KEY` | — | AWS secret access key |
| `S3_ENDPOINT` | `""` | Custom endpoint (MinIO local dev); empty = default AWS endpoint |

#### Scenario: Production blocks wildcard endpoint

- GIVEN `ENVIRONMENT=production` and `S3_ENDPOINT=""`
- WHEN Settings is loaded
- THEN no validation error is raised

#### Scenario: Custom endpoint used for MinIO

- GIVEN `S3_ENDPOINT="http://localhost:9000"` and `S3_BUCKET="rodeo-local"`
- WHEN `S3FileStorageService` is constructed
- THEN boto3 client connects to `http://localhost:9000`

### Requirement: Startup health check

The system MUST verify S3 connectivity at startup by calling `head_bucket` on the configured bucket. Failure MUST log a critical warning but NOT prevent app startup (same pattern as existing Redis health check).

#### Scenario: S3 bucket reachable logs info

- GIVEN valid S3 credentials and existing bucket
- WHEN the app starts
- THEN a log line `"S3 bucket '{bucket}' reachable"` is emitted at INFO level

#### Scenario: S3 bucket unreachable logs critical

- GIVEN invalid S3 credentials or missing bucket
- WHEN the app starts
- THEN a log line with CRITICAL level is emitted describing the failure
- AND the app continues to serve requests
