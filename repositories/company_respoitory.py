from sqlalchemy.future import select

from models import CompanyModel
from utils.repository import async_session


class CompanyRepository:
    """
    CompanyRepository is a class responsible for handling operations related to the CompanyModel.
    It provides methods for saving, updating, deleting, and retrieving company data from the database.
    """

    model = CompanyModel

    async def insert(self, company_info):
        """
        Asynchronously inserts a new company into the database.

        Parameters:
        - kwargs: Keyword arguments containing the company details.

        Returns:
        - None
        """

        async with async_session() as session:
            async with session.begin():
                company = self.model(**company_info)
                session.add(company)
                await session.commit()

        return company

    async def update_by_info(self, company_id: int, company_info):
        """
        Asynchronously updates a company's information in the database.

        Parameters:
        - company_id (int): The unique identifier for the company to be updated.
        - kwargs: Keyword arguments containing the new company details.

        Returns:
        - None
        """

        async with async_session() as session:
            async with session.begin():
                company = await session.execute(
                    select(self.model).where(self.model.id == company_id)
                )
                company = company.scalars().first()
                if company:
                    for attr, value in company_info.items():
                        setattr(company, attr, value)
                    await session.commit()
                else:
                    return None

    async def delete(self, company_id: int):
        """
        Asynchronously deletes a company from the database.

        Parameters:
        - company_id (int): The unique identifier for the company to be deleted.

        Returns:
        - None
        """

        async with async_session() as session:
            async with session.begin():
                company = await session.execute(
                    select(self.model).where(self.model.id == company_id)
                )
                company = company.scalars().first()
                if company:
                    session.delete(company)
                    await session.commit()
                else:
                    return None

    async def get_by_id(self, company_id: int):
        """
        Asynchronously retrieves a company by its ID from the database.

        Parameters:
        - company_id (int): The unique identifier for the company.

        Returns:
        - dict: A dictionary representing the company's data.
        """

        async with async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == company_id)
            )
            company = result.scalars().first()
            if company:
                return company
            else:
                return None

    async def get_all(self):
        """
        Asynchronously retrieves all companies from the database.

        Returns:
        - list: A list of dictionaries representing each company's data.
        """

        async with async_session() as session:
            result = await session.execute(select(self.model))
            companies = result.scalars().all()
            return [company for company in companies]

    async def get_by_company_id(self, company_id: int):
        """
        Asynchronously retrieves a company by its ID from the database.

        Parameters:
        - company_id (int): The unique identifier for the company.

        Returns:
        - dict: A dictionary representing the company's data.
        """

        return await self.get_by_id(company_id)

    async def get_by_company_url(self, company_url: str):
        """
        Asynchronously retrieves a company by its URL from the database.

        Parameters:
        - company_url (str): The unique URL for the company.

        Returns:
        - dict: A dictionary representing the company's data.
        """

        async with async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.company_url == company_url)
            )
            company = result.scalars().first()
            if company:
                return company
            else:
                return None
