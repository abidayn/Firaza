"""Request/response shapes (validated by Pydantic)."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class VendorIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    city: str = Field(default="", max_length=60)
    notes: str = ""


class VendorOut(VendorIn, ORM):
    id: int


class MaterialIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    category: str = "packaging"
    unit: str = "pcs"


class MaterialOut(MaterialIn, ORM):
    id: int


class VendorMaterialIn(BaseModel):
    vendor_id: int
    material_id: int
    unit_price: float = Field(gt=0)
    bulk_min_qty: int | None = Field(default=None, ge=1)
    bulk_unit_price: float | None = Field(default=None, gt=0)
    moq: int = Field(default=1, ge=1)
    lead_time_days: int = Field(ge=1, le=60)
    in_stock: bool = True
    quality_score: float = Field(ge=1, le=5)


class VendorMaterialOut(VendorMaterialIn, ORM):
    id: int


class TransactionIn(BaseModel):
    vendor_id: int
    material_id: int
    qty: int = Field(ge=1)
    unit_price: float = Field(gt=0)
    ordered_at: date
    promised_days: int = Field(ge=1, le=60)
    actual_days: int = Field(ge=0, le=365)
    defect_rate: float | None = Field(default=None, ge=0, le=1)


class TransactionOut(TransactionIn, ORM):
    id: int


class RecommendationIn(BaseModel):
    material_id: int
    qty: int = Field(ge=1, le=100000)
    deadline_days: int = Field(ge=1, le=30)
    w_price: float = Field(ge=0, le=1)
    w_speed: float = Field(ge=0, le=1)
    w_quality: float = Field(ge=0, le=1)


class RecommendationResult(BaseModel):
    rank: int
    vendor_id: int
    vendor_name: str
    score: float
    score_pct: float
    unit_price: float
    total_price: float
    lead_time_days: int
    quality_score: float
    ontime_rate: float
    defect_rate: float
    n_tx: int
    misses_deadline: bool
    below_moq: bool
    in_stock: bool
    contributions: dict[str, float]


class RecommendationOut(BaseModel):
    request_id: int
    material_id: int
    material_name: str
    qty: int
    deadline_days: int
    weights: dict[str, float]
    results: list[RecommendationResult]


class ExplanationOut(BaseModel):
    request_id: int
    text: str
    source: str
    model: str = ""
    sources: list[str] = []
