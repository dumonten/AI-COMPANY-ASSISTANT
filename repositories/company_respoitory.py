from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import delete, update

# Import the CompanyModel directly instead of through a module
from models import CompanyModel
from utils.repository import async_session


class CompanyRepository:
    # Removed the model attribute
    model = CompanyModel

    async def insert(self, company_info):
        # Create an instance of CompanyModel directly
        async with async_session() as session:
            async with session.begin():
                company_model = CompanyModel(**company_info)
                session.add(company_model)
                await session.commit()
        return company_model

    async def update_by_info(self, id, company_info):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(self.model).where(self.model.id == id).values(**company_info)
                )
                await session.commit()

    async def delete(self, id):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(self.model).where(self.model.id == id))
                await session.commit()

    async def get_by_id(self, id):
        async with async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == id)
            )
            return result.scalars().first()

    async def get_all(self):
        async with async_session() as session:
            result = await session.execute(select(self.model))
            return result.scalars().all()

    async def get_by_company_id(self, company_id):
        async with async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.id == company_id)
            )
            return result.scalars().first()

    async def get_by_company_url(self, company_url):
        async with async_session() as session:
            result = await session.execute(
                select(self.model).where(self.model.company_url == company_url)
            )
            return result.scalars().first()
