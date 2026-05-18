from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Common schemas
class SuccessResponse(BaseModel):
    message: str
    success: bool = True
