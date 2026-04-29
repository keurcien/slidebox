"""Exception hierarchy for slidebox.

Every error subclasses `SlideboxError` so callers can catch the library's
failures with a single except clause while still matching specific causes.
"""

from __future__ import annotations


class SlideboxError(Exception):
    """Base class for every slidebox error."""


class ValidationError(SlideboxError):
    """Invalid input at the component authoring boundary.

    Raised for things like malformed IDs, unsupported kwargs, or bad units.
    """


class LayoutError(SlideboxError):
    """The layout engine could not resolve bounds for a component.

    Usually means a child overflowed its parent or a fixed size
    exceeded the available canvas.
    """


class CompileError(SlideboxError):
    """The compiler refused to emit batchUpdate requests for the tree.

    Common causes: duplicate object IDs, unresolved bounds (layout skipped),
    or component kwargs that can't be translated into API requests.
    """


class AuthError(SlideboxError):
    """Credential resolution failed."""


class QuotaExceededError(SlideboxError):
    """Google Slides API rejected the request after retries were exhausted."""


class StaleStateError(SlideboxError):
    """Live deck state changed between query and update."""
