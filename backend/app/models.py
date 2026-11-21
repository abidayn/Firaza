"""Database tables."""
from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Vendor(Base):
    __tablename__ = "vendors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    city: Mapped[str] = mapped_column(String(60), default="")
    notes: Mapped[str] = mapped_column(Text, default="")


class Material(Base):
    __tablename__ = "materials"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    category: Mapped[str] = mapped_column(String(40), default="packaging")
    unit: Mapped[str] = mapped_column(String(20), default="pcs")


class VendorMaterial(Base):
    """One vendor's offer for one material."""
    __tablename__ = "vendor_materials"
    __table_args__ = (UniqueConstraint("vendor_id", "material_id"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    unit_price: Mapped[float] = mapped_column(Float)
    bulk_min_qty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bulk_unit_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    moq: Mapped[int] = mapped_column(Integer, default=1)
    lead_time_days: Mapped[int] = mapped_column(Integer)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)
    quality_score: Mapped[float] = mapped_column(Float)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    ordered_at: Mapped[date] = mapped_column(Date)
    promised_days: Mapped[int] = mapped_column(Integer)
    actual_days: Mapped[int] = mapped_column(Integer)
    defect_rate: Mapped[float | None] = mapped_column(Float, nullable=True)


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty: Mapped[int] = mapped_column(Integer)
    deadline_days: Mapped[int] = mapped_column(Integer)
    w_price: Mapped[float] = mapped_column(Float)
    w_speed: Mapped[float] = mapped_column(Float)
    w_quality: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("procurement_requests.id"))
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"))
    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)
    result_json: Mapped[str] = mapped_column(Text)   # full result row incl. feature contributions


class Explanation(Base):
    __tablename__ = "explanations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    request_id: Mapped[int] = mapped_column(ForeignKey("procurement_requests.id"), unique=True)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(30))   # llm | fallback | fallback_unverified
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    model: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
