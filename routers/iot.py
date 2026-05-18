from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_db
from models import IoTDevice, AlertnessReading, HealthRecord, User, AuditLog
from auth.dependencies import get_current_user
from auth.permissions import has_permission, MANAGE_IOT_DEVICES, VIEW_ALERTNESS_DATA

router = APIRouter()

# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

class DeviceRegisterRequest(BaseModel):
    name: str
    type: str          # Smartwatch, EEG Headset, Breathalyzer, Camera, Pulse Oximeter
    device_id: Optional[str] = None
    status: str = "active"
    battery: int = Field(100, ge=0, le=100)

class DeviceUpdateRequest(BaseModel):
    status: Optional[str] = None
    battery: Optional[int] = Field(None, ge=0, le=100)

class SensorReadingSubmit(BaseModel):
    device_id: str
    user_id: int
    # Vital signs
    heart_rate: Optional[float] = None
    oxygen_saturation: Optional[float] = None
    skin_temperature: Optional[float] = None
    hrv_score: Optional[float] = None
    # Alertness / EEG
    alertness_score: Optional[float] = Field(None, ge=0, le=100)
    fatigue_index: Optional[float] = Field(None, ge=0, le=100)
    eeg_theta_power: Optional[float] = None
    eeg_alpha_power: Optional[float] = None
    blink_rate: Optional[float] = None
    eye_closure_duration: Optional[float] = None
    # Reaction / cognitive
    reaction_time_ms: Optional[float] = None
    cognitive_load: Optional[float] = Field(None, ge=0, le=100)
    attention_score: Optional[float] = Field(None, ge=0, le=100)

class DeviceResponse(BaseModel):
    id: int
    name: str
    type: str
    status: str
    battery: int
    last_sync: datetime
    device_id: str
    created_at: datetime

    class Config:
        from_attributes = True

# ──────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────

def _classify_alertness(score: float) -> tuple:
    if score >= 80:
        return "high", False
    elif score >= 60:
        return "moderate", False
    elif score >= 40:
        return "low", True
    else:
        return "critical", True

# ──────────────────────────────────────────────
# DEVICE MANAGEMENT ENDPOINTS
# ──────────────────────────────────────────────

@router.get("/devices", response_model=List[DeviceResponse])
def get_iot_devices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all registered IoT devices."""
    return db.query(IoTDevice).order_by(IoTDevice.name).all()


@router.post("/devices/register", response_model=DeviceResponse, status_code=status.HTTP_201_CREATED)
def register_device(
    data: DeviceRegisterRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Register a new IoT health sensor device."""
    if not has_permission(current_user, MANAGE_IOT_DEVICES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    import uuid
    device_id = data.device_id or str(uuid.uuid4())

    if db.query(IoTDevice).filter(IoTDevice.device_id == device_id).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Device ID already registered.")

    device = IoTDevice(
        name=data.name,
        type=data.type,
        status=data.status,
        battery=data.battery,
        device_id=device_id,
    )
    db.add(device)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="iot_device_registered",
        resource_type="iot_device",
        resource_id=device_id,
        action_details=f"Device registered: {data.name} ({data.type}) ID: {device_id}",
        module="Health Sensors",
        success=True,
    ))
    db.commit()
    db.refresh(device)
    return device


@router.put("/devices/{device_id}")
def update_device(
    device_id: str,
    data: DeviceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update device status or battery level."""
    if not has_permission(current_user, MANAGE_IOT_DEVICES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    device = db.query(IoTDevice).filter(IoTDevice.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    if data.status:
        device.status = data.status
    if data.battery is not None:
        device.battery = data.battery
    device.last_sync = datetime.utcnow()
    db.commit()
    return {"message": "Device updated.", "device_id": device_id}


@router.delete("/devices/{device_id}")
def decommission_device(
    device_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Decommission (remove) an IoT device."""
    if not has_permission(current_user, MANAGE_IOT_DEVICES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied.")

    device = db.query(IoTDevice).filter(IoTDevice.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found.")

    db.delete(device)
    db.add(AuditLog(
        user_id=current_user.id,
        action_type="iot_device_decommissioned",
        resource_type="iot_device",
        resource_id=device_id,
        action_details=f"Device {device.name} ({device_id}) decommissioned",
        module="Health Sensors",
        success=True,
    ))
    db.commit()
    return {"message": f"Device {device_id} decommissioned."}


# ──────────────────────────────────────────────
# SENSOR DATA ENDPOINTS
# ──────────────────────────────────────────────

@router.post("/readings", status_code=status.HTTP_201_CREATED)
def submit_sensor_reading(
    data: SensorReadingSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Ingest a sensor reading from an IoT health device.
    Automatically creates AlertnessReading if alertness_score provided.
    Also creates HealthRecord for vital sign data.
    """
    # Verify device exists and update last sync
    device = db.query(IoTDevice).filter(IoTDevice.device_id == data.device_id).first()
    if device:
        device.last_sync = datetime.utcnow()

    records_created = []

    # Create AlertnessReading if alertness data present
    if data.alertness_score is not None:
        alertness_level, risk_flag = _classify_alertness(data.alertness_score)
        reading = AlertnessReading(
            user_id=data.user_id,
            alertness_score=data.alertness_score,
            fatigue_index=data.fatigue_index,
            reaction_time_ms=data.reaction_time_ms,
            blink_rate=data.blink_rate,
            eye_closure_duration=data.eye_closure_duration,
            cognitive_load=data.cognitive_load,
            attention_score=data.attention_score,
            heart_rate=data.heart_rate,
            hrv_score=data.hrv_score,
            eeg_theta_power=data.eeg_theta_power,
            eeg_alpha_power=data.eeg_alpha_power,
            source=f"iot_{device.type.lower().replace(' ', '_')}" if device else "iot_device",
            device_id=data.device_id,
            alertness_level=alertness_level,
            risk_flag=risk_flag,
        )
        db.add(reading)
        records_created.append("alertness_reading")

    # Create HealthRecord if vital signs present
    if any([data.heart_rate, data.oxygen_saturation, data.hrv_score]):
        health = HealthRecord(
            user_id=data.user_id,
            heart_rate=data.heart_rate,
            oxygen_saturation=data.oxygen_saturation,
            alertness_score=data.alertness_score,
            reaction_time_ms=data.reaction_time_ms,
            notes=f"Auto-ingested from IoT device: {data.device_id}",
        )
        db.add(health)
        records_created.append("health_record")

    db.add(AuditLog(
        user_id=current_user.id,
        action_type="iot_reading_ingested",
        resource_type="sensor_reading",
        resource_id=data.device_id,
        action_details=f"IoT data ingested for user {data.user_id} | Created: {', '.join(records_created)}",
        module="Health Sensors",
        success=True,
    ))
    db.commit()

    return {
        "message": "Sensor reading ingested successfully.",
        "records_created": records_created,
        "device_id": data.device_id,
        "user_id": data.user_id,
    }


@router.get("/readings/{user_id}")
def get_sensor_readings(
    user_id: int,
    hours: int = Query(24, le=168),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get recent sensor readings for a user."""
    if not has_permission(current_user, VIEW_ALERTNESS_DATA) and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    cutoff = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(AlertnessReading).filter(
        AlertnessReading.user_id == user_id,
        AlertnessReading.reading_timestamp >= cutoff,
        AlertnessReading.source.like("iot_%"),
    ).order_by(desc(AlertnessReading.reading_timestamp)).all()

    return {
        "user_id": user_id,
        "period_hours": hours,
        "total_readings": len(readings),
        "readings": [
            {
                "timestamp": r.reading_timestamp,
                "alertness_score": r.alertness_score,
                "alertness_level": r.alertness_level,
                "fatigue_index": r.fatigue_index,
                "heart_rate": r.heart_rate,
                "hrv_score": r.hrv_score,
                "risk_flag": r.risk_flag,
                "device_id": r.device_id,
                "source": r.source,
            }
            for r in readings
        ],
    }


@router.get("/fleet-health")
def get_fleet_health_sensors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Fleet-wide sensor and device health overview."""
    if not has_permission(current_user, MANAGE_IOT_DEVICES):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    devices = db.query(IoTDevice).all()
    active = [d for d in devices if d.status == "active"]
    low_battery = [d for d in devices if d.battery < 20]

    # Devices not synced in last hour
    stale_cutoff = datetime.utcnow() - timedelta(hours=1)
    stale = [d for d in active if d.last_sync < stale_cutoff]

    # Recent IoT readings in last hour
    readings_1h = db.query(AlertnessReading).filter(
        AlertnessReading.reading_timestamp >= stale_cutoff,
        AlertnessReading.source.like("iot_%"),
    ).count()

    return {
        "devices": {
            "total": len(devices),
            "active": len(active),
            "inactive": len([d for d in devices if d.status == "inactive"]),
            "charging": len([d for d in devices if d.status == "charging"]),
            "low_battery": len(low_battery),
            "stale_not_synced_1h": len(stale),
        },
        "by_type": {
            t: sum(1 for d in devices if d.type == t)
            for t in set(d.type for d in devices)
        },
        "readings_last_hour": readings_1h,
        "low_battery_devices": [
            {"name": d.name, "device_id": d.device_id, "battery": d.battery} for d in low_battery
        ],
    }
