from pydantic import BaseModel, field_validator


class BillingDataCreate(BaseModel):
    billing_address: str
    tax_id: str | None = None
    currency: str = "USD"

    @field_validator("currency")
    def validate_currency(cls, v):
        if v not in ["USD"]:
            raise ValueError("Currency must be USD")
        return v


class BillingDataUpdate(BaseModel):
    billing_address: str | None = None
    tax_id: str | None = None
    currency: str | None = None

    @field_validator("currency")
    def validate_currency(cls, v):
        if v not in ["USD"]:
            raise ValueError("Currency must be USD")
        return v


class BillingDataResponse(BaseModel):
    id: str
    user_id: str
    billing_address: str
    tax_id: str
    balance: float
    currency: str

    class Config:
        from_attributes = True
