from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
import models, schemas, auth

router = APIRouter(prefix="/constats", tags=["constats"])


@router.post("/", response_model=schemas.ConstatOut)
def create_constat(
    constat: schemas.ConstatCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    new_constat = models.Constat(**constat.model_dump(), user_id=current_user.id)
    db.add(new_constat)
    db.commit()
    db.refresh(new_constat)
    return new_constat


@router.get("/", response_model=List[schemas.ConstatOut])
def list_constats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # admin sees everyone's, regular user sees only their own
    query = db.query(models.Constat).order_by(models.Constat.created_at.desc())
    if current_user.role == "admin":
        return query.all()
    return query.filter(models.Constat.user_id == current_user.id).all()


@router.get("/{constat_id}", response_model=schemas.ConstatOut)
def get_constat(
    constat_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    constat = db.query(models.Constat).filter(models.Constat.id == constat_id).first()
    if not constat:
        raise HTTPException(status_code=404, detail="Constat not found")
    if constat.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to view this constat")
    return constat


@router.put("/{constat_id}/report", response_model=schemas.ConstatOut)
def save_constat_report(
    constat_id: int,
    report: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    """Save the analysis output for one constat.

    The owner can save their own result and an admin can correct or replace any
    result.  The report is included automatically in the history responses.
    """
    constat = db.query(models.Constat).filter(models.Constat.id == constat_id).first()
    if not constat:
        raise HTTPException(status_code=404, detail="Constat not found")
    if constat.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this constat")

    constat.analysis_report = report
    db.commit()
    db.refresh(constat)
    return constat
