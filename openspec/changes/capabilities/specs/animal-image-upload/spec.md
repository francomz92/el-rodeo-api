# Animal Image Upload Specification

## Purpose

Enable users to upload images and associate them with animal records. The image is stored in S3 under a tenant-scoped key and the animal record gets an updated image URL. This is the first domain use case consuming `IFileStorageService`.

## Requirements

### Requirement: UploadAnimalImageUseCase

The system MUST provide an `UploadAnimalImageUseCase` that accepts an animal ID, tenant ID, file bytes, filename, and content type. It SHALL:

1. Verify the animal exists and belongs to the requesting tenant.
2. Generate an S3 key: `animals/{tenant_id}/{animal_id}/{uuid4}.{ext}`.
3. Upload the file via `IFileStorageService.upload()`.
4. Update the animal's `image_url` field in the database.
5. Return `{"url": "...", "key": "..."}`.

#### Scenario: Happy path — upload succeeds

- GIVEN an existing animal with id `"abc-123"` belonging to tenant `"t1"`
- WHEN `UploadAnimalImageUseCase` is called with valid JPEG bytes and filename `"photo.jpg"`
- THEN the file is uploaded to S3 with key matching `animals/t1/abc-123/{uuid}.jpg`
- AND the animal's `image_url` is set to the returned URL
- AND the response contains `{"url": "https://...", "key": "animals/t1/abc-123/{uuid}.jpg"}`

#### Scenario: Animal not found raises error

- GIVEN no animal exists with id `"missing-id"` for the requesting tenant
- WHEN `UploadAnimalImageUseCase` is called
- THEN an `AnimalNotFoundError` is raised

#### Scenario: Upload failure propagates error

- GIVEN an existing animal and `IFileStorageService.upload()` raises `S3FileStorageError`
- WHEN `UploadAnimalImageUseCase` is called
- THEN the error propagates unmodified
- AND the animal's `image_url` is NOT updated

### Requirement: POST /cattle/animals/{id}/images endpoint

The system MUST expose a `POST /cattle/animals/{id}/images` endpoint accepting `multipart/form-data` with a single `file` field. The endpoint SHALL:

- Require `EDITOR` role or higher.
- Accept files up to 10 MB.
- Reject non-image content types (MIME must start with `image/`).
- Return HTTP 201 on success with `{"url": "...", "key": "..."}`.

#### Scenario: Successful image upload returns 201

- GIVEN an authenticated user with `EDITOR` role and an existing animal
- WHEN a `POST /cattle/animals/{id}/images` is sent with a valid JPEG file
- THEN the response status is 201
- AND the body contains `url` and `key` fields

#### Scenario: Non-image file rejected with 400

- GIVEN an authenticated user with `EDITOR` role
- WHEN a `POST /cattle/animals/{id}/images` is sent with a `text/plain` file
- THEN the response status is 400
- AND the error message indicates the file must be an image

#### Scenario: File over 10 MB rejected with 413

- GIVEN an authenticated user with `EDITOR` role
- WHEN a `POST /cattle/animals/{id}/images` is sent with a file exceeding 10 MB
- THEN the response status is 413

#### Scenario: Non-existent animal returns 404

- GIVEN an authenticated user with `EDITOR` role
- WHEN a `POST /cattle/animals/{id}/images` is sent with a non-existent animal ID
- THEN the response status is 404
- AND the error indicates the animal was not found

### Requirement: S3 key naming convention

All animal image uploads MUST use the key pattern `animals/{tenant_id}/{animal_id}/{uuid}.{ext}`. The file extension SHALL be derived from the uploaded filename (last segment after `.`). If no extension is present, `"bin"` SHALL be used.

#### Scenario: Extension derived from filename

- GIVEN filename `"photo.PNG"`
- WHEN the S3 key is generated
- THEN the key ends with `.png` (lowercased)
