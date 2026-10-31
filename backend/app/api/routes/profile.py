from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.services.profile import (
    ProfileDatabaseError,
    ProfileNotFoundError,
    get_profile,
    update_profile,
)


router = APIRouter(prefix="/profile", tags=["profile"])


def _profile_error(error: ProfileDatabaseError) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Profile service unavailable",
    )


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    try:
        return get_profile(db, current_user.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found") from error
    except ProfileDatabaseError as error:
        raise _profile_error(error) from error


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    changes: ProfileUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    if not changes.model_fields_set:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No profile changes provided")
    try:
        return update_profile(db, current_user.id, changes.display_name)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found") from error
    except ProfileDatabaseError as error:
        raise _profile_error(error) from error
