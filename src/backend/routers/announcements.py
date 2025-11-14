"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, Optional, List
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


@router.get("", response_model=List[Dict[str, Any]])
@router.get("/", response_model=List[Dict[str, Any]])
def get_announcements(
    active_only: bool = Query(True, description="Filter for active announcements only")
) -> List[Dict[str, Any]]:
    """
    Get all announcements, with optional filtering for active announcements only
    
    - active_only: If True, only return active announcements that haven't expired
    """
    query = {}
    
    if active_only:
        current_date = datetime.now().strftime("%Y-%m-%d")
        query = {
            "is_active": True,
            "$or": [
                {"expiration_date": {"$gte": current_date}},
                {"expiration_date": None}
            ]
        }
    
    announcements = []
    for announcement in announcements_collection.find(query).sort("created_at", -1):
        # Convert ObjectId to string for JSON serialization
        announcement["_id"] = str(announcement["_id"])
        announcements.append(announcement)
    
    return announcements


@router.post("/", response_model=Dict[str, Any])
def create_announcement(
    message: str,
    expiration_date: str,
    teacher_username: str = Query(..., description="Username of the teacher creating the announcement"),
    start_date: Optional[str] = Query(None, description="Optional start date for the announcement")
) -> Dict[str, Any]:
    """Create a new announcement - requires teacher authentication"""
    
    # Check teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate required fields
    if not message or not message.strip():
        raise HTTPException(
            status_code=400, detail="Message is required")
    
    if not expiration_date:
        raise HTTPException(
            status_code=400, detail="Expiration date is required")
    
    # Validate date format
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Create announcement document
    announcement = {
        "message": message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": teacher_username,
        "created_at": datetime.now().isoformat() + "Z",
        "is_active": True
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return {
        "message": "Announcement created successfully",
        "announcement": announcement
    }


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    message: str,
    expiration_date: str,
    teacher_username: str = Query(..., description="Username of the teacher updating the announcement"),
    start_date: Optional[str] = Query(None, description="Optional start date for the announcement"),
    is_active: bool = Query(True, description="Whether the announcement is active")
) -> Dict[str, Any]:
    """Update an existing announcement - requires teacher authentication"""
    
    # Check teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate announcement exists
    try:
        announcement = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID")
    
    if not announcement:
        raise HTTPException(
            status_code=404, detail="Announcement not found")
    
    # Validate required fields
    if not message or not message.strip():
        raise HTTPException(
            status_code=400, detail="Message is required")
    
    if not expiration_date:
        raise HTTPException(
            status_code=400, detail="Expiration date is required")
    
    # Validate date format
    try:
        datetime.strptime(expiration_date, "%Y-%m-%d")
        if start_date:
            datetime.strptime(start_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    # Update announcement
    update_data = {
        "message": message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
        "is_active": is_active
    }
    
    result = announcements_collection.update_one(
        {"_id": ObjectId(announcement_id)},
        {"$set": update_data}
    )
    
    # No need to check result.modified_count; document existence is already validated.
    
    return {"message": "Announcement updated successfully"}


@router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: str,
    teacher_username: str = Query(..., description="Username of the teacher deleting the announcement")
) -> Dict[str, Any]:
    """Delete an announcement - requires teacher authentication"""
    
    # Check teacher authentication
    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(
            status_code=401, detail="Invalid teacher credentials")
    
    # Validate announcement exists
    try:
        announcement = announcements_collection.find_one({"_id": ObjectId(announcement_id)})
    except:
        raise HTTPException(
            status_code=400, detail="Invalid announcement ID")
    
    if not announcement:
        raise HTTPException(
            status_code=404, detail="Announcement not found")
    
    # Delete announcement
    result = announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=500, detail="Failed to delete announcement")
    
    return {"message": "Announcement deleted successfully"}