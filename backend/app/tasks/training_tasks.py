"""
Background training tasks, run via Celery so the admin's "Train AI Model"
button returns instantly instead of blocking an HTTP request for the
duration of training.
"""
from __future__ import annotations

from app.core.celery_app import celery_app


@celery_app.task(name="tasks.retrain_vision_model")
def retrain_vision_model_task() -> dict:
    """
    Retrains the vision classifier bundle. In its current form this trains
    on the synthetic demo dataset (see app/services/vision/synthetic_dataset.py);
    once the admin's Image Dataset Builder has accumulated enough
    doctor-verified real images (ImageRecord rows with is_verified=True),
    swap the data source in scripts/train_vision_model.py to pull from
    those instead — the rest of this task and the inference pipeline
    require no changes.
    """
    import subprocess
    import sys
    from pathlib import Path

    backend_dir = Path(__file__).resolve().parent.parent.parent
    result = subprocess.run(
        [sys.executable, str(backend_dir / "scripts" / "train_vision_model.py")],
        cwd=str(backend_dir),
        capture_output=True,
        text=True,
        timeout=1800,
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout[-4000:],
        "stderr": result.stderr[-2000:] if result.returncode != 0 else "",
    }
