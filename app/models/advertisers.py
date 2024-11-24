from sqlalchemy import Column, ForeignKey, Integer, String

from app.models import Base
from app.utils.cuid import generate_cuid


class Advertiser(Base):
    __tablename__ = "advertisers"
    id = Column(String, autoincrement=False, primary_key=True, default=generate_cuid)

    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)

    advertisement_id = Column(Integer, ForeignKey("advertisements.id"))
    campaign_id = Column(Integer, ForeignKey("campaigns.id"))
