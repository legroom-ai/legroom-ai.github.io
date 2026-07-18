"""Evaluation runners for different scenarios."""

from legroom.evals.runners.before_after import BeforeAfterRunner
from legroom.evals.runners.compression_only import CompressionOnlyRunner

__all__ = ["BeforeAfterRunner", "CompressionOnlyRunner"]
