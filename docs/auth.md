# Authentication

Slidebox accepts four auth paths, in priority order:

1. **Pass-through credentials** — build a `google.oauth2.Credentials` object yourself and pass it in.
2. **Service account file** — point at a SA JSON key.
3. **OAuth client secrets** — runs the installed-app flow on a local port (interactive).
4. **Application Default Credentials** — falls through to `gcloud auth application-default login`, GCE metadata, Cloud Run env creds, etc.

## Pass-through

```python
from google.oauth2.credentials import Credentials
creds = Credentials(token=..., refresh_token=...)
Presentation(credentials=creds)
```

## Service account

```python
Presentation(service_account_file="/path/to/sa.json")
```

Make sure the service account has been shared into the target Drive folder, and that the Slides API is enabled in the project.

## OAuth

```python
Presentation(oauth_client_secrets="client_secrets.json")
```

First run opens a browser for consent. Subsequent runs cache the token.

## ADC

```python
Presentation()        # no args → ADC
```

Works out of the box on Cloud Run, GCE, GKE workload identity, or after `gcloud auth application-default login` on a dev machine.

## Scopes

Default: `presentations` + `drive.file`. Pass `scopes=(...)` if you need more.
