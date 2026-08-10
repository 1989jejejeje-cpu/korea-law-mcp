import os
import ssl
from typing import Any

import httpx
import truststore
from dotenv import load_dotenv


load_dotenv()

LAW_API_OC = os.getenv("LAW_API_OC")

if not LAW_API_OC:
    raise RuntimeError(
        "LAW_API_OC 환경변수가 없습니다. .env 파일을 확인하세요."
    )

BASE_URL = "https://www.law.go.kr/DRF"
TIMEOUT = 30.0


# Windows 시스템 인증서 저장소 사용
SSL_CONTEXT = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)


async def _get_json(
    endpoint: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """
    국가법령정보 Open API를 호출하고 JSON을 반환한다.
    """

    request_params = {
        "OC": LAW_API_OC,
        "type": "JSON",
        **params,
    }

    url = f"{BASE_URL}/{endpoint}"

    async with httpx.AsyncClient(
        timeout=TIMEOUT,
        follow_redirects=True,
        verify=SSL_CONTEXT,
    ) as client:
        response = await client.get(
            url,
            params=request_params,
        )

        response.raise_for_status()

        return response.json()


async def search_law_api(
    query: str,
    page: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """
    현행 법령을 법령명으로 검색한다.
    """

    return await _get_json(
        "lawSearch.do",
        {
            "target": "law",
            "query": query,
            "page": page,
            "display": num_of_rows,
        },
    )


async def get_law_api(
    *,
    mst: str | None = None,
    law_id: str | None = None,
) -> dict[str, Any]:
    """
    법령 전체 본문을 조회한다.
    MST 또는 법령ID 중 하나를 사용한다.
    """

    if not mst and not law_id:
        raise ValueError("mst 또는 law_id 중 하나가 필요합니다.")

    params: dict[str, Any] = {
        "target": "law",
    }

    if mst:
        params["MST"] = mst

    if law_id:
        params["ID"] = law_id

    return await _get_json(
        "lawService.do",
        params,
    )


def _article_code(number: int) -> str:
    if number < 1:
        raise ValueError("조 번호는 1 이상이어야 합니다.")

    return f"{number:04d}00"


def _sub_article_code(number: int) -> str:
    if number < 1:
        raise ValueError("번호는 1 이상이어야 합니다.")

    return f"{number:04d}00"


async def get_article_api(
    *,
    law_id: str,
    article: int,
    article_sub: int | None = None,
    paragraph: int | None = None,
    item: int | None = None,
    mok: str | None = None,
) -> dict[str, Any]:
    """
    법령의 특정 조·항·호·목을 조회한다.
    """

    if article_sub is None:
        jo = _article_code(article)
    else:
        if article < 1 or article_sub < 1:
            raise ValueError("조 번호는 1 이상이어야 합니다.")

        jo = f"{article:04d}{article_sub:02d}"

    params: dict[str, Any] = {
        "target": "lawjosub",
        "ID": law_id,
        "JO": jo,
    }

    if paragraph is not None:
        params["HANG"] = _sub_article_code(paragraph)

    if item is not None:
        params["HO"] = _sub_article_code(item)

    if mok is not None:
        params["MOK"] = mok

    return await _get_json(
        "lawService.do",
        params,
    )