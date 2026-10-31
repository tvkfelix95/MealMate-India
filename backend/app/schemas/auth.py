from pydantic import BaseModel


class AuthenticatedUserResponse(BaseModel):
    id: str


class AuthCredentials(BaseModel):
    email: str
    password: str


class AuthSessionResponse(BaseModel):
    user_id: str
    access_token: str | None = None
    refresh_token: str | None = None
    email_confirmation_required: bool = False
