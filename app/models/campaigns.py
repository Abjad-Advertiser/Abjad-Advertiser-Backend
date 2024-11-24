from sqlalchemy import Column, String

from app.models import Base
from app.utils.cuid import generate_cuid


class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(String, autoincrement=False, primary_key=True, default=generate_cuid)
