from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql.expression import delete, update

from models import CompanyModel
from utils.repository import async_session


class CompanyRepository:
    model = CompanyModel

    @classmethod
    async def insert(
        cls,
        company_name=None,
        company_url=None,
        web_site_raw_data=None,
        web_site_summary_data=None,
        assistant_id=None,
    ):
        company = CompanyModel(
            company_name=company_name,
            company_url=company_url,
            web_site_raw_data=web_site_raw_data,
            web_site_summary_data=web_site_summary_data,
            assistant_id=assistant_id,
        )
        async with async_session() as session:
            async with session.begin():
                session.add(company)
                await session.commit()

    @classmethod
    async def update_by_company(cls, company_instance: CompanyModel):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls.model)
                    .where(cls.model.id == company_instance.id)
                    .values(**company_instance.to_dict())
                )
                await session.commit()

    @classmethod
    async def update_by_info(cls, id, company_info):
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    update(cls.model).where(cls.model.id == id).values(**company_info)
                )
                await session.commit()

    @classmethod
    async def delete(cls, id):
        async with async_session() as session:
            async with session.begin():
                await session.execute(delete(cls.model).where(cls.model.id == id))
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
    async def get_by_company_assistant_id(cls, assistant_id):
        async with async_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.assistant_id == assistant_id)
            )
            return result.scalars().first()

    @classmethod
    async def get_by_company_url(cls, company_url):
        async with async_session() as session:
            result = await session.execute(
                select(cls.model).where(cls.model.company_url == company_url)
            )
            return result.scalars().first()
