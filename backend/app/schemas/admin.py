from pydantic import BaseModel


class AdminBootstrapResponse(BaseModel):
    message: str
