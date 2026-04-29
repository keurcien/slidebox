"""Compile a resolved component tree into Google Slides batchUpdate requests."""

from __future__ import annotations

from slidebox.compile.compiler import BatchPlan, Compiler
from slidebox.compile.ids import IdAllocator
from slidebox.compile.metadata import decode_metadata, encode_metadata

__all__ = ["BatchPlan", "Compiler", "IdAllocator", "decode_metadata", "encode_metadata"]
