from sqlalchemy import Column, Integer, String, ForeignKey, Float


from app.db.db_session import Base
from app.models.users import Credentials
from app.utils.cuid import generate_cuid

class BillingData(Base):
    __tablename__ = "billing_datas"
    
    id = Column(Integer, autoincrement=False,primary_key=True, index=True, default=generate_cuid)
    user_id = Column(Integer, ForeignKey(Credentials.id), unique=True, index=True)
    
    billing_address = Column(String(200))
    tax_id = Column(String(20))
    balance = Column(Float, default=0.0, nullable=False)