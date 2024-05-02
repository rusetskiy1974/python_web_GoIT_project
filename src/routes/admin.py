from fastapi import APIRouter, HTTPException, Depends, Path
from src.schemas.user import UserReadSchema
from src.models.models import User, Role
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository.users import get_user_by_email
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])


@router.put("/users/{user_id}/status", dependencies=[Depends(role_admin)])
async def change_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(auth_service.get_current_user)
):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.is_active = is_active
    await user.save()
    
    return {"message": f"User status changed to {'active' if is_active else 'inactive'}."}


@router.put("/{email}/unblock", response_model=UserReadSchema, dependencies=[Depends(role_admin)])
async def unblock_user_by_email(
    email: str = Path(..., title="The email of the user to unblock"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Get the user by email from the database
    user = await get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Set the user's is_active status to True to unblock the user
    user.is_active = True
    await db.commit()

    return user