from app.models.user import User, Collector
from app.models.waste import WasteSubmission, WasteItem, AreaCollection
from app.models.facility import WasteFacility, WasteGenerationZone
from app.models.prediction import WastePrediction, AreaPrediction, OverflowRiskPrediction, PredictionAccuracy, ActualCollection, TrainingReferenceStats

__all__ = [
    "User",
    "Collector",
    "WasteSubmission",
    "WasteItem",
    "AreaCollection",
    "WasteFacility",
    "WasteGenerationZone",
    "WastePrediction",
    "AreaPrediction",
    "OverflowRiskPrediction",
    "PredictionAccuracy",
    "TrainingReferenceStats",
    "ActualCollection",
]