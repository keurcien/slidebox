"""Credential resolution.

`resolve_credentials` walks this priority chain:

    1. `credentials` kwarg (already-built google-auth Credentials)
    2. `access_token` (raw OAuth access token, optionally with refresh
       material for auto-refresh)
    3. `service_account_file` (path to a SA JSON key)
    4. `oauth_client_secrets` (path to an OAuth client-secrets JSON;
       runs the installed-app flow on a local port)
    5. Application Default Credentials (`gcloud auth application-default`,
       GCE metadata service, Cloud Run, etc.)

This hybrid approach matches the user's chosen "managed + pass-through"
auth strategy: sophisticated callers hand in their own creds; casual
users can point at a file or rely on ADC.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from slidebox.errors import AuthError

if TYPE_CHECKING:
    pass  # pragma: no cover

DEFAULT_SCOPES: tuple[str, ...] = (
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
)


def resolve_credentials(
    *,
    credentials: Any | None = None,
    access_token: str | None = None,
    refresh_token: str | None = None,
    token_uri: str | None = None,
    client_id: str | None = None,
    client_secret: str | None = None,
    service_account_file: str | None = None,
    oauth_client_secrets: str | None = None,
    scopes: tuple[str, ...] = DEFAULT_SCOPES,
) -> Any:
    """Return a Google-auth Credentials object ready for the API client."""
    if credentials is not None:
        return credentials

    if access_token is not None:
        try:
            from google.oauth2.credentials import Credentials as UserCredentials
        except ImportError as exc:  # pragma: no cover
            raise AuthError("google-auth is required for OAuth token auth") from exc
        return UserCredentials(  # type: ignore[no-untyped-call]
            token=access_token,
            refresh_token=refresh_token,
            token_uri=token_uri or "https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=list(scopes),
        )

    if service_account_file is not None:
        try:
            from google.oauth2.service_account import Credentials as SACredentials
        except ImportError as exc:  # pragma: no cover
            raise AuthError("google-auth is required for service-account auth") from exc
        return SACredentials.from_service_account_file(  # type: ignore[no-untyped-call]
            service_account_file, scopes=list(scopes)
        )

    if oauth_client_secrets is not None:
        try:
            from google_auth_oauthlib.flow import InstalledAppFlow
        except ImportError as exc:  # pragma: no cover
            raise AuthError("google-auth-oauthlib is required for OAuth flow") from exc
        flow = InstalledAppFlow.from_client_secrets_file(  # type: ignore[no-untyped-call]
            oauth_client_secrets, list(scopes)
        )
        return flow.run_local_server(port=0)

    # Application Default Credentials.
    try:
        import google.auth  # pragma: no cover
    except ImportError as exc:  # pragma: no cover
        raise AuthError("google-auth is required for ADC") from exc
    try:
        creds, _project = google.auth.default(scopes=list(scopes))
        return creds
    except Exception as exc:  # pragma: no cover - environment-specific
        raise AuthError(
            "Could not resolve credentials. Pass `credentials=`, "
            "`access_token=`, `service_account_file=`, "
            "`oauth_client_secrets=`, or set up ADC."
        ) from exc
