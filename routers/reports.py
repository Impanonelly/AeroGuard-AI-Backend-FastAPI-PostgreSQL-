from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth.dependencies import get_current_user
from auth.permissions import (
    require_safety_officer_or_above,
    VIEW_REPORTS,
    GENERATE_REPORTS,
    has_permission
)
from services.pdf_generator import generate_compliance_report
from datetime import datetime

router = APIRouter()

@router.get("/compliance/pdf", response_class=Response)
def download_compliance_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Exports a professional Safety & Compliance PDF Report.
    SRS Requirement 8.1: Restricted to Safety Officers or Admins.
    """
    # 1. Permission Check (SRS Requirement 8.1)
    if not has_permission(current_user, GENERATE_REPORTS):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied. You do not have permission to generate compliance reports."
        )

    # 2. Fetch Data (Unified Personnel Status for the report)
    from models import UserRole, FitnessAssessment, AlcoholScreening, SubstanceScreening
    from sqlalchemy import func

    # Subqueries for latest assessment/clearance
    latest_fitness = db.query(
        FitnessAssessment.user_id,
        FitnessAssessment.clearance_status,
        func.max(FitnessAssessment.assessment_date).label("max_date")
    ).group_by(FitnessAssessment.user_id).subquery()

    pilots = db.query(User).filter(User.role == UserRole.AVIATOR).all()
    
    # Enrich objects for the PDF generator (keeping it simple for now)
    for p in pilots:
        # Fetch latest fitness
        fit = db.query(FitnessAssessment).filter(FitnessAssessment.user_id == p.id).order_by(FitnessAssessment.assessment_date.desc()).first()
        p.clearance_status = fit.clearance_status if fit else "pending"
        p.risk_level = "LOW" # Default for report if not calculated
        if fit and fit.clearance_status == "grounded": p.risk_level = "HIGH"

    if not pilots:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No personnel records found to generate report."
        )

    # 3. Generate PDF
    pdf_content = generate_compliance_report(pilots, current_user.full_name)
    
    # 4. Return as a downloadable attachment
    filename = f"AeroGuard_Compliance_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
