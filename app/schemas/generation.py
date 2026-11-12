# app/schemas/generation.py
from pydantic import BaseModel
from typing import Optional, Dict, Any

class GenerationResponse(BaseModel):
    code: int
    msg: str
    data: Optional[Dict[str, Any]] = None

# 如果需要更精细的请求模型，也可以加