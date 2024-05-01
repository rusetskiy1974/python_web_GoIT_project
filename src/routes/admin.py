from fastapi import APIRouter, HTTPException, Depends
from src.models import User, Role
from src.services.auth import get_current_user
from src.services.role import RoleAccess

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])


@router.put("/users/{user_id}/status", dependencies=[Depends(role_admin)])
async def change_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(get_current_user)
):
    user = await User.get(id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    user.is_active = is_active
    await user.save()
    
    return {"message": f"User status changed to {'active' if is_active else 'inactive'}."}