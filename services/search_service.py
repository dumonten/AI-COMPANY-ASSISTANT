import json
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

import requests
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import TokenTextSplitter
from loguru import logger

from config import settings

logger.add("loggger.log")


class SearchService:
    _config = {
        "search_model": "gpt-4o",
        "search_temperature": 0.5,
        "search_prompt_template": """
            Вы журналист и исследователь мирового уровня.
            Вы очень хорошо умеете находить наиболее релевантные статьи по определенной теме;
            {response}
            Выше приведен список результатов поиска по запросу {query}.
            Пожалуйста, выберите {articles_count} лучшие статьи из списка, 
            верните ТОЛЬКО массив URL-адресов, больше ничего не добавляйте. 
        """,
        "summarize_prompt_model": "gpt-4o",
        "summarize_prompt_temperature": 0.1,
        "summarize_prompt_template": """
            Сейчас я буду давать тебе информацию с сайта {url} про компанию в следующем формате: 
            1) Уже накопленная тобой информация с сайта.
            2) Новая информация с сайта.
            Твоя задача - накапливать информацию о компании, очищая текст от лишнего и оставляя только самое важное.
            Если некоторая информация из накопленной информация повторяется в новой информации, 
            то не добавляй её снова. Просто объедини их, обобщив суть из накопленной информации и новой информации. 
            Твоя накопленная информация:
            {summary_text}. 
            Новая информация с сайта:
            {text}
        """,
        "summarize_chunk_size": 48000,
        "summarize_chunk_overlap": 500,
        "crawler_parameters": {
            "crawlerOptions": {
                "excludes": ["blog/*"],
                "maxDepth": 2,
                "includes": [],
                "limit": 5,
            },
            "pageOptions": {"onlyMainContent": False},
        },
    }

    @staticmethod
    async def _clean_text(text: str) -> str:
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
        text = re.sub(r"!\[.*\]\(.*\)", "", text)
        text = re.sub(r"\!\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"\[.*?\]\(.*?\)", "", text)
        text = re.sub(r"<img.*?>", "", text)
        text = re.sub(r"<a.*?>|</a>", "", text)
        text = re.sub(r"\*+", "", text)
        text = re.sub(r"#", "", text)
        text = re.sub(r"=", "", text)
        text = re.sub(r"-", "", text)
        text = re.sub(r"\\", "", text)
        text = re.sub(
            r"\b\w+\.(jpg|jpeg|png|gif|bmp|pdf|doc|docx|xls|xlsx|ppt|pptx|webp)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"[\"']", "", text)
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    @staticmethod
    async def _check_if_valid(url: str) -> bool:
        try:
            response: Optional[requests.Response] = requests.get(url, stream=True)
            if response.status_code == 200:
                logger.info(f"{url}: url is valid.")
                return True
            else:
                logger.error(f"{url}: url is notvalid.")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(
                f"{url}: url is notvalid. Error occurred while accessing the website: {e}."
            )
            return False

    @staticmethod
    async def get_content_from_urls(
        urls: List[str], timeout: float = 0.5, jobs_limit: int = 3
    ) -> Tuple[List[str], List[List[str]]]:

        async def _check_job(
            jobId: str,
            all_data: List[str],
            all_source_urls: List[List[str]],
            timeout: float,
        ) -> bool:
            api = f"https://api.firecrawl.dev/v0/crawl/status/{jobId}"
            headers = {"Authorization": f"Bearer {settings.FIRE_CRAWL_KEY}"}
            response: requests.Response = requests.request("GET", api, headers=headers)

            if response.status_code == 200:
                response_json = response.json()
                status = response_json["status"]
                if status == "completed":
                    data = []
                    source_urls = []
                    if (
                        isinstance(response_json["data"], list)
                        and len(response_json["data"]) > 0
                    ):
                        for result in response_json["data"]:
                            source_urls.append(result["metadata"]["sourceURL"])
                            data.append(result["markdown"])
                        data = "\n".join(data)
                        data = await SearchService._clean_text(data)
                        logger.info(f"Job with id {jobId} data:\n{data}")
                        logger.info(f"Job with id {jobId} source URLs:\n{source_urls}")
                        all_data.append(data)
                        all_source_urls.append(source_urls)
                    else:
                        if len(response_json["data"]) == 0:
                            logger.error(f"Crawl job ended with empty data")
                        else:
                            logger.error(
                                f'Crawl job ended with error: {response_json["data"]["error"]}'
                            )
                    return True
                elif status in ["active", "paused", "pending", "queued"]:
                    time.sleep(timeout)
                    return False
                else:
                    api = f"https://api.firecrawl.dev/v0/crawl/cancel/{jobId}"
                    headers = {"Authorization": f"Bearer {settings.FIRE_CRAWL_KEY}"}
                    response: requests.Response = requests.request(
                        "DELETE", api, headers=headers
                    )
                    logger.error(f"Crawl job failed or was stopped. Status: {status}")
                    return True

        all_data: List[str] = []
        all_source_urls: List[List[str]] = []

        jobs: Set[str] = set()
        jobs_to_remove: Set[str] = set()

        for url in urls:
            crawl_job_id = settings.firecrawl_app.crawl_url(
                url,
                params=SearchService._config["crawler_parameters"],
                wait_until_done=False,
            )

            jobs.add(crawl_job_id["jobId"])

            logger.info(f"Current Job Id: {crawl_job_id['jobId']}")

            while len(jobs) == jobs_limit:
                for jobId in jobs:
                    if await _check_job(jobId, all_data, all_source_urls, timeout):
                        jobs_to_remove.add(jobId)
                jobs = jobs.difference(jobs_to_remove)

        while len(jobs) > 0:
            for jobId in jobs:
                if await _check_job(jobId, all_data, all_source_urls, timeout):
                    jobs_to_remove.add(jobId)
            jobs = jobs.difference(jobs_to_remove)

        return all_data, all_source_urls

    @classmethod
    async def search_articles(cls, query: str, articles_count: int) -> List[str]:

        async def _find_best_article_urls(
            response_json: Dict[str, Any], query: str, articles_count: int
        ) -> List[Dict[str, str]]:
            llm = ChatOpenAI(
                openai_api_key=settings.OPENAI_KEY,
                model_name=cls._config["search_model"],
                temperature=cls._config["search_temperature"],
            )

            prompt = PromptTemplate.from_template(cls._config["search_prompt_template"])
            chain = prompt | llm | StrOutputParser()
            urls = chain.invoke(
                {
                    "response": response_json,
                    "query": query,
                    "articles_count": articles_count,
                }
            )
            return json.loads(urls)

        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {"X-API-KEY": settings.SER_KEY, "Content-Type": "application/json"}
        response = requests.request("POST", url, headers=headers, data=payload)

        urls = await _find_best_article_urls(response, query, articles_count)

        return urls

    @classmethod
    async def summarize_content(cls, url: str, source_texts: List[str]) -> str:
        if source_texts is None:
            return None

        llm = ChatOpenAI(
            openai_api_key=settings.OPENAI_KEY,
            model_name=cls._config["summarize_prompt_model"],
            temperature=cls._config["summarize_prompt_temperature"],
        )

        prompt = PromptTemplate.from_template(cls._config["summarize_prompt_template"])
        chain = prompt | llm | StrOutputParser()

        text_splitter = TokenTextSplitter(
            chunk_size=cls._config["summarize_chunk_size"],
            chunk_overlap=cls._config["summarize_chunk_overlap"],
        )

        summary_text = ""

        for text in source_texts:
            chunks = text_splitter.split_text(text)
            for chunk in chunks:
                summary_text = chain.invoke(
                    {"summary_text": summary_text, "text": chunk, "url": url}
                )
                logger.info(f"Summary text:\n{summary_text}\n")

        return summary_text
