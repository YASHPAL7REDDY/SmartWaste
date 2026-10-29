"""
Compatibility module for loading pickled models.
Provides the TwoStageModel class at the expected import path.
"""

from app.services.ml_shared import TwoStageModel

__all__ = ["TwoStageModel"]