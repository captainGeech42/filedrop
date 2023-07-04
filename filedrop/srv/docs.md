# v1 API Docs

Authenticate by putting the API key in the `X-Filedrop-Key` header.

## File Management

### POST `/api/v1/file/new`

Upload a new file

### GET `/api/v1/file/<uuid>`

Get the metadata for a file

### GET `/api/v1/file/<uuid>/details`

Get the detailed metadata for a file, only accessible by the uploader (if not-anon, otherwise inaccessible)


### GET `/api/v1/file/<uuid>/download`

Download a file