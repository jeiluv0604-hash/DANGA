# -*- coding: utf-8 -*-
from typing import Literal, Optional

from pydantic import BaseModel, Field


class ActionTransitionRequest(BaseModel):
    new_status: Literal["IN_PROGRESS", "CLOSED", "VERIFIED", "BLOCKED", "REOPENED", "CANCELLED"]
    actor_role: str = Field(min_length=2, max_length=64)
    comment: Optional[str] = Field(default=None, max_length=1000)

