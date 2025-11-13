"""
ML model management routes.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks

from orchestrator.services.ml_prediction import MLPredictionService

logger = logging.getLogger(__name__)

router = APIRouter()
ml_service = MLPredictionService()

@router.get("/")
async def get_model_status():
    """Get current ML model status and metrics."""
    try:
        status = await ml_service.get_model_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get model status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/retrain")
async def retrain_model(background_tasks: BackgroundTasks):
    """Trigger ML model retraining."""
    try:
        # Run retraining in background
        background_tasks.add_task(_retrain_model_background)

        return {
            "status": "started",
            "message": "Model retraining started in background"
        }
    except Exception as e:
        logger.error(f"Failed to start model retraining: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_model_metrics():
    """Get detailed model performance metrics."""
    try:
        status = await ml_service.get_model_status()

        # Add more detailed metrics
        metrics = {
            "model_status": status,
            "performance_indicators": {
                "min_training_samples": 50,
                "target_mape": 0.15,  # 15% MAPE target
                "retraining_frequency": "daily"
            },
            "feature_importance": [],  # Would be populated from model
            "prediction_distribution": {
                "low_confidence": "< 0.3",
                "medium_confidence": "0.3-0.7",
                "high_confidence": "> 0.7"
            }
        }

        return metrics
    except Exception as e:
        logger.error(f"Failed to get model metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _retrain_model_background():
    """Background task for model retraining."""
    try:
        logger.info("Starting background model retraining")

        result = await ml_service.retrain_model()

        if result["status"] == "success":
            logger.info(f"Model retraining completed successfully. Train MAPE: {result['train_mape']:.4f}")
        else:
            logger.warning(f"Model retraining failed: {result.get('message', 'Unknown error')}")

    except Exception as e:
        logger.error(f"Background model retraining failed: {e}")
