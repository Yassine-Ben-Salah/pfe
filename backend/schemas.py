from pydantic import BaseModel, EmailStr
from typing  import Optional
from datetime import datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    username: str
    telephone: str
    role: str  = "user"  # Default role is "user"

class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    telephone: str
    role: str
    is_active: bool
    

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    telephone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None 


class ConstatCreate(BaseModel):
    file_id: Optional[str] = None
    full_text: Optional[str] = None
    page_count: Optional[int] = None
    blurred_pdf_url: Optional[str] = None

    date_accident: Optional[str] = None
    heure: Optional[str] = None
    lieu: Optional[str] = None
    blesses: Optional[str] = None

    vehicule_a_marque: Optional[str] = None
    vehicule_a_type: Optional[str] = None
    vehicule_a_immatriculation: Optional[str] = None
    assurance_a: Optional[str] = None
    degats_vehicule_a: Optional[str] = None

    vehicule_b_marque: Optional[str] = None
    vehicule_b_type: Optional[str] = None
    vehicule_b_immatriculation: Optional[str] = None
    assurance_b: Optional[str] = None
    degats_vehicule_b: Optional[str] = None

    observations: Optional[str] = None
    analysis_report: Optional[dict] = None


class ConstatOut(ConstatCreate):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True
