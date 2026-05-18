from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class NotificationCreate(BaseModel):
    title: str
    message: str
    notification_type: str = "alert"
    priority: str = "medium"
    action_required: bool = False

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    notification_type: str
    priority: str
    status: str
    action_required: bool
    action_taken: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
