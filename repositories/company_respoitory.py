from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import delete, update

from models import CompanyModel
from utils.repository import async_session


class CompanyRepository:
    model = CompanyModel

    @classmethod
    async def insert(cls, company_info):

        cls.model = CompanyModel(**company_info)
        async with async_session() as session:
            async with session.begin():
                session.add(cls.model)
                await session.commit()
        return cls.model

    @classmethod
    async def update_by_info(cls, id, company_info):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls.model.__table__)
                    .where(cls.model.id == id)
                    .values(**company_info)
                )
                await session.commit()

    @classmethod
    async def delete(cls, id):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    delete(cls.model.__table__).where(cls.model.id == id)
                )
                await session.commit()

    @classmethod
    async def get_by_id(cls, id):
        async with async_session() as session:
            result = await session.execute(select(cls.model).where(cls.model.id == id))
            return result.scalars().first()

    @classmethod
    async def get_all(cls):
        async with async_session() as session:
            result = await session.execute(select(cls.model))
            return result.scalars().all()

    @classmethod
    async def get_by_company_id(cls, company_id):
        async with async_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.id == company_id)
            )
            return result.scalars().first()

    @classmethod
    async def get_by_company_url(cls, company_url):
        async with async_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.company_url == company_url)
            )
            return result.scalars().first()
