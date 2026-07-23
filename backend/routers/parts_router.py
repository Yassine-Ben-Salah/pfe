from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import SessionLocal
import models

router = APIRouter(prefix="/parts", tags=["parts"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("")
def list_parts(
    q: Optional[str] = Query(None),
    brand: Optional[str] = Query(None),
    car_name: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(models.CarPart)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                models.CarPart.piece_name.ilike(term),
                models.CarPart.piece_brand.ilike(term),
                models.CarPart.car_name.ilike(term),
                models.CarPart.brand.ilike(term),
            )
        )

    if brand:
        query = query.filter(models.CarPart.brand.ilike(f"%{brand}%"))

    if car_name:
        query = query.filter(models.CarPart.car_name.ilike(f"%{car_name}%"))

    rows = query.order_by(models.CarPart.id.desc()).offset(offset).limit(limit).all()

    return {
        "items": [
            {
                "id": row.id,
                "motorisation_id": row.motorisation_id,
                "brand": row.brand,
                "car_name": row.car_name,
                "piece_name": row.piece_name,
                "piece_brand": row.piece_brand,
                "piece_price": row.piece_price,
            }
            for row in rows
        ],
        "limit": limit,
        "offset": offset,
        "count": len(rows),
    }