from sqlalchemy import Column, String

from app.models import Base
from app.utils.cuid import generate_cuid


class Advertisement(Base):
    __tablename__ = "advertisements"
    id = Column(String, autoincrement=False, primary_key=True, default=generate_cuid)

    title = Column(String, nullable=True)
    description = Column(String, nullable=True)
    media = Column(String, nullable=True)
    target_audience = Column(String, nullable=True)
    budget_allocation = Column(String, nullable=True)
