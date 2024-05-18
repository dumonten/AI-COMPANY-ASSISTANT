from sqlalchemy import Column, Integer, String

from utils.repository import Base


class CompanyModel(Base):
    """
    Represents a company entity in the database, capturing essential details about a company.
    """

    __tablename__ = "company"

    """
    Primary key column for uniquely identifying each company record.
    """
    id = Column(Integer, primary_key=True)

    """
    Column to store the name of the company.
    """
    company_name = Column(String)

    """
    Column to store the unique URL of the company.
    """
    company_url = Column(String, unique=True)

    """
    Column to store raw data fetched from the company's website (data after crawling).
    """
    web_site_raw_data = Column(String)

    """
    Column to store a summary of the company's website content (made by AI).
    """
    web_site_summary_data = Column(String)

    """
    Column to store the unique identifier for the assistant associated with the company. 
    """
    assistant_id = Column(String, unique=True)

    """
    Column to store the unique URL associated with the assistant. 
    """
    assistant_url = Column(String, unique=True)

    def to_dict(self):
        """
        Converts the CompanyModel instance into a dictionary representation,
        suitable for serialization or API responses.

        Returns:
        dict: A dictionary containing the company's details.
        """
        return {
            "company_name": self.company_name,
            "company_url": self.company_url,
            "web_site_raw_data": self.web_site_raw_data,
            "web_site_summary_data": self.web_site_summary_data,
            "assistant_id": self.assistant_id,
            "assistant_url": self.assistant_url,
        }
