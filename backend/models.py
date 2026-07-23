from sqlalchemy import Column, Float, Integer, String, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    role = Column(String, default="user")
    username = Column(String, unique=True, index=True, nullable=False)
    telephone = Column(String, unique=True, index=True, nullable=False)
    constats = relationship("Constat", back_populates="owner")


class Constat(Base):
    __tablename__ = "constats"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # from process-constat
    file_id = Column(String, nullable=True)
    full_text = Column(Text, nullable=True)
    page_count = Column(Integer, nullable=True)
    blurred_pdf_url = Column(String, nullable=True)

    # from extract-fields
    date_accident = Column(String, nullable=True)
    heure = Column(String, nullable=True)
    lieu = Column(String, nullable=True)
    blesses = Column(String, nullable=True)

    vehicule_a_marque = Column(String, nullable=True)
    vehicule_a_type = Column(String, nullable=True)
    vehicule_a_immatriculation = Column(String, nullable=True)
    assurance_a = Column(String, nullable=True)
    degats_vehicule_a = Column(Text, nullable=True)

    vehicule_b_marque = Column(String, nullable=True)
    vehicule_b_type = Column(String, nullable=True)
    vehicule_b_immatriculation = Column(String, nullable=True)
    assurance_b = Column(String, nullable=True)
    degats_vehicule_b = Column(Text, nullable=True)

    observations = Column(Text, nullable=True)

    # Final claim analysis returned after the constat is processed.
    # Keeping it on the constat makes each history entry self-contained.
    analysis_report = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    owner = relationship("User", back_populates="constats")


class CarPart(Base):
    __tablename__ = "car_parts"

    id = Column(Integer, primary_key=True, index=True)
    motorisation_id = Column(String, index=True, nullable=True)
    car_name = Column(String, index=True, nullable=False)
    brand = Column(String, index=True, nullable=False)
    piece_name = Column(String, index=True, nullable=False)
    piece_brand = Column(String, nullable=True)
    piece_price = Column(Float, nullable=True)
