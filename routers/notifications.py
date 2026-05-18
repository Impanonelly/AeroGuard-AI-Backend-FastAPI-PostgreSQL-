from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from database import get_db
from models import User, Notification
from auth.dependencies import get_current_user
from auth.permissions import require_supervisor_or_above
from schemas.notification import NotificationResponse

router = APIRouter()

@router.post("/broadcast", status_code=status.HTTP_201_CREATED)
def broadcast_alert(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_supervisor_or_above)
):
    """
    Generate an emergency broadcast notification for all active users.
    Only Supervisors, Safety Officers, or Admins can perform this action.
    """
    active_users = db.query(User).filter(User.is_active == True).all()
    
    notifications = []
    timestamp = datetime.utcnow()
    for user in active_users:
        # Generate the notification
        notification = Notification(
            user_id=user.id,
            title="SYSTEM BROADCAST",
            message="Emergency broadcast successfully sent to all active crew members.",
            notification_type="critical",
            priority="critical",
            status="unread",
            action_required=False,
            created_at=timestamp
        )
        notifications.append(notification)
        db.add(notification)
    
    db.commit()
    return {"message": f"Broadcast sent to {len(notifications)} users."}


@router.post("/archive", status_code=status.HTTP_200_OK)
def archive_all_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Archive (mark as read) all notifications for the current user.
    """
    notifications = db.query(Notification).filter(
        Notification.user_id == current_user.id,
        Notification.status == "unread"
    ).all()
    
    for notification in notifications:
        notification.status = "read"
        notification.read_at = datetime.utcnow()
        
    db.commit()
    return {"message": "All unread notifications archived successfully."}


@router.get("/", response_model=List[NotificationResponse])
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all notifications for the current user, ordered by most recent.
    """
    return db.query(Notification).filter(
        Notification.user_id == current_user.id
    ).order_by(Notification.created_at.desc()).all()
