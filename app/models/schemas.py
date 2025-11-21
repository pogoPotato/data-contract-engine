from __future__ import annotations
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID
import yaml
from pydantic import BaseModel, Field, validator, ConfigDict

# --- Internal Schema Models (Parsed from YAML) ---

class FieldDefinition(BaseModel):
    type: str
    required: bool = True
    pattern: Optional[str] = None
    format: Optional[str] = None
    min: Optional[Union[int, float, str]] = None
    max: Optional[Union[int, float, str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    description: Optional[str] = None
    enum: Optional[List[Any]] = None
    items: Optional["FieldDefinition"] = None  # For arrays
    properties: Optional[Dict[str, "FieldDefinition"]] = None  # For objects

class ContractSchema(BaseModel):
    contract_version: str
    domain: str
    description: Optional[str] = None
    schema: Dict[str, FieldDefinition] = Field(..., alias="schema")
    quality_rules: Optional[Dict[str, Any]] = None

# --- API Request/Response Models ---

class ContractCreate(BaseModel):
    name: str = Field(..., min_length=3, max_length=255, pattern=r"^[a-zA-Z0-9-]+$")
    domain: str = Field(..., min_length=2, max_length=100)
    yaml_content: str
    description: Optional[str] = None

    @validator("yaml_content")
    def validate_yaml_syntax(cls, v):
        try:
            parsed = yaml.safe_load(v)
            if not isinstance(parsed, dict):
                raise ValueError("YAML must parse to a dictionary")
            if "contract_version" not in parsed:
                raise ValueError("Missing required key: contract_version")
            if "schema" not in parsed:
                raise ValueError("Missing required key: schema")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        return v

class ContractUpdate(BaseModel):
    yaml_content: str
    description: Optional[str] = None
    
    @validator("yaml_content")
    def validate_yaml_syntax(cls, v):
        # Re-use logic or import from util if complex
        try:
            parsed = yaml.safe_load(v)
            if not isinstance(parsed, dict):
                raise ValueError("YAML must parse to a dictionary")
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax: {e}")
        return v

class ContractResponse(BaseModel):
    id: UUID
    name: str
    version: str
    domain: str
    yaml_content: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ContractList(BaseModel):
    contracts: List[ContractResponse]
    total: int
    page: int
    page_size: int
    has_next: bool