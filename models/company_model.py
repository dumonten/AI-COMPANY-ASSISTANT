from sqlalchemy import Column, Integer, String

from utils.repository import Base


class CompanyModel(Base):

    __tablename__ = "company"

    id = Column(Integer, primary_key=True)

    company_name = Column(String)
    company_url = Column(String, unique=True)

    web_site_raw_data = Column(String)
    web_site_summary_data = Column(String)

    assistant_id = Column(String, unique=True)
