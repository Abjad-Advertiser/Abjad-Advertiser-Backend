from pydantic import BaseModel


class BillingDataCreate(BaseModel):
    billing_address: str
    tax_id: str | None = None
    currency: str = "USD"


class BillingDataUpdate(BaseModel):
    billing_address: str | None = None
    tax_id: str | None = None
    currency: str | None = None


class BillingDataResponse(BaseModel):
    id: str
    user_id: str
    billing_address: str
    tax_id: str
    balance: float
    currency: str

    class Config:
        from_attributes = True
