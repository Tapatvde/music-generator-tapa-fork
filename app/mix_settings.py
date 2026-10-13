"""Validated opt-in mix processing; importable without the audio runtime."""
from pydantic import BaseModel, Field


class MixSettings(BaseModel):
    vocals: bool = False
    backing: bool = False
    vocal_db: float = Field(0, ge=-6, le=6, allow_inf_nan=False)
    backing_db: float = Field(0, ge=-6, le=6, allow_inf_nan=False)

    def active(self):
        return self.vocals or self.backing or self.vocal_db != 0 or self.backing_db != 0
