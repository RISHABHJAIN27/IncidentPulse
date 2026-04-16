from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
import uuid


class SeverityLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class IncidentStatus(str, Enum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"


class IncidentCreate(BaseModel):
    title: str
    severity: SeverityLevel


class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.investigating
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IncidentUpdate(BaseModel):
    status: IncidentStatus