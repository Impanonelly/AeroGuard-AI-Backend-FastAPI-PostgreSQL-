from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import MedicalRecord, User, UserRole, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, VIEW_MEDICAL_RECORDS, CREATE_MEDICAL_RECORDS, VIEW_CREW_DATA

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class MedicalRecordCreate(BaseModel):
    user_id: int
    examination_type: str = "annual"
    examining_physician: Optional[str] = None
    medical_facility: Optional[str] = None
    medical_class: Optional[str] = None         # "Class 1", "Class 2", "Class 3"
    certificate_number: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    clearance_status: str = "cleared"

    vision_ok: bool = True
    hearing_ok: bool = True
    cardiovascular_ok: bool = True
    neurological_ok: bool = True
    respiratory_ok: bool = True
    musculoskeletal_ok: bool = True
    psychiatric_ok: bool = True

    limitations: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordUpdate(BaseModel):
    clearance_status: Optional[str] = None
    valid_until: Optional[datetime] = None
    limitations: Optional[str] = None
    conditions: Optional[str] = None
    medications: Optional[str] = None
    notes: Optional[str] = None

class MedicalRecordResponse(BaseModel):
    id: int
    user_id: int
    record_date: datetime
    examination_type: str
    examining_physician: Optional[str]
    medical_facility: Optional[str]
    medical_class: Optional[str]
    certificate_number: Optional[str]
    valid_from: Optional[datetime]
    valid_until: Optional[datetime]
    clearance_status: str
    vision_ok: bool
    hearing_ok: bool
    cardiovascular_ok: bool
    neurological_ok: bool
    respiratory_ok: bool
    musculoskeletal_ok: bool
    psychiatric_ok: bool
    limitations: Optional[str]
    conditions: Optional[str]
    medications: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/", response_model=MedicalRecordResponse, status_code=status.HTTP_201_CREATED)
def create_medical_record(
    data: MedicalRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a formal medical record. Medical Officer or Administrator only."""
    if not has_permission(current_user, CREATE_MEDICAL_RECORDS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Medical Officer role required.")

    record = MedicalRecord(
        user_id=data.user_id,
        examination_type=data.examination_type,
        examining_physician=data.examining_physician,
        medical_facility=data.medical_facility,
        medical_class=data.medical_class,
        certificate_number=data.certificate_number,
        valid_from=data.valid_from,
        valid_until=data.valid_until,
        clearance_status=data.clearance_status,
        vision_ok=data.vision_ok,
        hearing_ok=data.hearing_ok,
        cardiovascular_ok=data.cardiovascular_ok,
        neurological_ok=data.neurological_ok,
        respiratory_ok=data.respiratory_ok,
        musculoskeletal_ok=data.musculoskeletal_ok,
        psychiatric_ok=data.psychiatric_ok,
        limitations=data.limitations,
        conditions=data.conditions,
        medications=data.medications,
        notes=data.notes,
        created_by=current_user.id,
    )
    db.add(record)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="medical_record_created",
        resource_type="medical_record",
        resource_id=str(data.user_id),
        action_details=f"Medical record created by {current_user.full_name} | Class: {data.medical_class} | Status: {data.clearance_status}",
        module="Medical Records",
        success=True,
    ))
    db.commit()
    db.refresh(record)
    return record


@router.get("/user/{user_id}", response_model=List[MedicalRecordResponse])
def get_medical_records(
    user_id: int,
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get medical records for a user. Medical Officer / Administrator / Owner user."""
    if not has_permission(current_user, VIEW_MEDICAL_RECORDS) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied. Medical records are confidential.")

    records = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.user_id == user_id)
        .order_by(desc(MedicalRecord.record_date))
        .limit(limit)
        .all()
    )
    return records


@router.get("/latest/{user_id}", response_model=MedicalRecordResponse)
def get_latest_medical_record(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the most recent medical record for a user."""
    can_view = has_permission(current_user, VIEW_MEDICAL_RECORDS) or has_permission(current_user, VIEW_CREW_DATA) or current_user.id == user_id
    if not can_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    record = (
        db.query(MedicalRecord)
        .filter(MedicalRecord.user_id == user_id)
        .order_by(desc(MedicalRecord.record_date))
        .first()
    )
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No medical records found.")
    return record


@router.put("/{record_id}", response_model=MedicalRecordResponse)
def update_medical_record(
    record_id: int,
    data: MedicalRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an existing medical record."""
    if not has_permission(current_user, CREATE_MEDICAL_RECORDS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Medical Officer role required.")

    record = db.query(MedicalRecord).filter(MedicalRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medical record not found.")

    for field, value in data.dict(exclude_unset=True).items():
        setattr(record, field, value)
    record.updated_at = datetime.utcnow()

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="medical_record_updated",
        resource_type="medical_record",
        resource_id=str(record_id),
        action_details=f"Medical record updated by {current_user.full_name}",
        module="Medical Records",
        success=True,
    ))
    db.commit()
    db.refresh(record)
    return record


@router.get("/clearances")
def get_active_clearances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all active medical clearances with expiry status."""
    if not has_permission(current_user, VIEW_MEDICAL_RECORDS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    now = datetime.utcnow()
    soon = now + timedelta(days=30)

    records = db.query(MedicalRecord).filter(
        MedicalRecord.clearance_status == "cleared"
    ).order_by(desc(MedicalRecord.valid_until)).all()

    result = []
    for r in records:
        status_flag = "valid"
        if r.valid_until and r.valid_until < now:
            status_flag = "expired"
        elif r.valid_until and r.valid_until < soon:
            status_flag = "expiring_soon"

        result.append({
            "record_id": r.id,
            "user_id": r.user_id,
            "medical_class": r.medical_class,
            "certificate_number": r.certificate_number,
            "valid_until": r.valid_until,
            "clearance_status": r.clearance_status,
            "expiry_status": status_flag,
        })

    return {"clearances": result, "total": len(result)}
