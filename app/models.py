from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid

class Severitylevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"

class IncidentStatus(str, Enum):
    investigating = "investigating"
    identified = "identified"
    monitoring = "monitoring"
    resolved = "resolved"

class Incident(BaseModel):
    title = str   
    severity = Severitylevel

class Incident(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    severity: SeverityLevel
    status: IncidentStatus = IncidentStatus.investigating
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
class IncidentUpdate(BaseModel):
    status: IncidentStatus
