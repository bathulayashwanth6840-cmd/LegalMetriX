from fastapi import Request, Depends
from sqlalchemy.orm import Session
from . import database, models, auth
from typing import Optional

def log_audit(db: Session, user_id: Optional[int], action: str, entity_type: str, entity_id: int):
    """
    Utility function to record audit logs.
    Will be used by routes that create/update/delete Scans or Reports.
    """
    audit_log = models.AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id
    )
    db.add(audit_log)
    db.commit()

async def audit_logger_dependency(request: Request, db: Session = Depends(database.get_db)):
    """
    A dependency that can be injected into routes to provide an easy way to log.
    In FastAPI, it's often easier to explicitly call a log function in the route 
    handler if we need the newly created entity's ID, rather than pure middleware 
    which doesn't easily have access to the response body IDs.
    """
    pass # Currently handled as a utility function call in the routes
