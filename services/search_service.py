import json
import os
import re
import time
import uuid
from typing import Any, Dict, List

import requests
import streamlit as st
from bs4 import BeautifulSoup
from dotenv import find_dotenv, load_dotenv
from firecrawl import FirecrawlApp
from langchain.chains import LLMChain
from langchain_community.document_loaders import UnstructuredURLLoader
from langchain_core.callbacks import FileCallbackHandler
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_text_splitters import CharacterTextSplitter, TokenTextSplitter
from loguru import logger

from config import settings


class SearchService:
    # A dictionary containing configuration options for the speech service, such as the model and voice to use.
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
            Если некоторая информация повторяется, то оставь её в единственном экземпляре. 
            Твоя накопленная информация:
            {summary_text}. 
            Новая информация с сайта:
            {text}
        """,
        "summarize_chunk_size": 32000,
        "summarize_chunk_overlap": 500,
    }

    @staticmethod
    def _clean_text(text: str) -> str:
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
        text = re.sub(
            r"\b\w+\.(jpg|jpeg|png|gif|bmp|pdf|doc|docx|xls|xlsx|ppt|pptx|webp)\b",
            "",
            text,
            flags=re.IGNORECASE,
        )
        text = re.sub(r"\s+", " ", text)
        text = text.strip()
        return text

    @staticmethod
    def _check_if_valid(url: str) -> bool:
        try:
            response = requests.get(url, stream=True)
            if response.status_code == 200:
                logger.info(f"{url} - is Valid.")
                return True
            else:
                logger.error(f"{url} - IS NOT VALID.")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(
                f"{url} - IS NOT VALID. Error occured while accessing to web site: {e}."
            )
            return False

    @staticmethod
    def get_content_from_urls(
        urls: List[str], timeout: int = 0.5, jobs_limit: int = 3
    ) -> List[str]:

        all_data = []
        all_source_urls = []

        jobs = set()
        jobs_to_remove = set()

        for url in urls:
            if not SearchService._check_if_valid(url):
                continue
            crawl_job_id = app.crawl_url(
                url, params=crawl_params, wait_until_done=False
            )
            jobs.add(crawl_job_id["jobId"])
            while len(jobs) == jobs_limit:
                for jobId in jobs:
                    if check_job(jobId, all_data, all_source_urls, timeout):
                        jobs_to_remove.add(jobId)
                jobs = jobs.difference(jobs_to_remove)
        while len(jobs) > 0:
            for jobId in jobs:
                if check_job(jobId, all_data, all_source_urls, timeout):
                    jobs_to_remove.add(jobId)
            jobs = jobs.difference(jobs_to_remove)
        return all_data, all_source_urls

    @classmethod
    def search_articles(cls, query: str, articles_count: int) -> List[str]:

        def _find_best_article_urls(
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

        urls = _find_best_article_urls(response, query, articles_count)

        return urls

    @classmethod
    def summarize_content(cls, url: str) -> str:
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

        for d in data:
            texts = text_splitter.split_text(d)
            for text in texts:
                summary_text = chain.invoke(
                    {"summary_text": summary_text, "text": text, "url": url}
                )
                logger.info(f"summary_text:\n\n{summary_text}\n\n")

        return summary_text
