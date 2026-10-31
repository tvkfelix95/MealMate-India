from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import AuthenticatedUser
from app.db.session import get_db
from app.schemas.preferences import PreferencesResponse, PreferencesUpdate
from app.services.preferences import (
    PreferencesDatabaseError,
    PreferencesNotFoundError,
    PreferencesValidationError,
    get_preferences,
    save_preferences,
)


router = APIRouter(prefix="/preferences", tags=["preferences"])


def _preference_error(error: PreferencesDatabaseError) -> HTTPException:
    return HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Preference service unavailable")


@router.get("/me", response_model=PreferencesResponse)
def get_my_preferences(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    try:
        return get_preferences(db, current_user.id)
    except PreferencesNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preferences not found") from error
    except PreferencesDatabaseError as error:
        raise _preference_error(error) from error


@router.put("/me", response_model=PreferencesResponse)
def put_my_preferences(
    changes: PreferencesUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesResponse:
    try:
        return save_preferences(db, current_user.id, changes)
    except PreferencesValidationError as error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)) from error
    except PreferencesNotFoundError as error:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found") from error
    except PreferencesDatabaseError as error:
        raise _preference_error(error) from error
