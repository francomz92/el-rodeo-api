"""Pydantic schemas for report query parameters."""

from datetime import date, timedelta

from pydantic import BaseModel, field_validator, model_validator


class SalesSummaryQuery(BaseModel):
    """Query parameters for the sales summary report.

    Requires a date range with a maximum span of 365 days.
    """

    from_date: date
    to_date: date

    @field_validator("to_date")
    @classmethod
    def validate_range(cls, v: date, info) -> date:
        from_val = info.data.get("from_date")
        if from_val is not None and (v - from_val) > timedelta(days=365):
            raise ValueError("Date range must not exceed 365 days")
        return v

    @model_validator(mode="after")
    def _validate_date_order(self) -> "SalesSummaryQuery":
        if self.from_date > self.to_date:
            raise ValueError("from_date must be on or before to_date")
        return self
