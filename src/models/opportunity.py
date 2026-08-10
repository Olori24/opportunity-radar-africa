from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text

from src.database.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(255))

    organization = Column(String(255))

    country = Column(String(255))

    category = Column(String(255))

    deadline = Column(String(255))

    url = Column(String(500))

    description = Column(Text)
