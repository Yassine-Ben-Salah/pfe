# ingest_parts.py
import ijson
from decimal import Decimal, InvalidOperation
from database import SessionLocal
import models

BATCH_SIZE = 5000

def parse_price(raw: str) -> float | None:
    if not raw:
        return None
    try:
        return float(Decimal(raw))
    except (InvalidOperation, ValueError):
        return None

def ingest(json_path: str):
    db = SessionLocal()
    batch = []
    total = 0

    with open(json_path, "rb") as f:
        for car in ijson.items(f, "item"):
            motorisation_id = car.get("motorisation_id")
            car_name = car.get("car_name", "").strip()
            brand = car.get("brand", "").strip()

            for piece in car.get("pieces", []):
                batch.append(models.CarPart(
                    motorisation_id=motorisation_id,
                    car_name=car_name,
                    brand=brand,
                    piece_name=(piece.get("piece_name") or "").strip(),
                    piece_brand=(piece.get("piece_brand") or "").strip() or None,
                    piece_price=parse_price(piece.get("piece_price")),
                ))

            if len(batch) >= BATCH_SIZE:
                db.bulk_save_objects(batch)
                db.commit()
                total += len(batch)
                print(f"Inserted {total} rows...")
                batch.clear()

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
        total += len(batch)

    print(f"Done. Total rows inserted: {total}")
    db.close()

if __name__ == "__main__":
    import sys
    ingest(sys.argv[1])