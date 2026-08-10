from typing import Any

from fastmcp import FastMCP

from law_api import (
    get_article_api,
    get_law_api,
    search_law_api,
)


mcp = FastMCP(
    "Korea Law MCP"
)


@mcp.tool
async def search_law(
    query: str,
    page: int = 1,
    num_of_rows: int = 20,
) -> dict[str, Any]:
    """
    대한민국 현행 법령을 법령명으로 검색합니다.

    Use this when the user wants to find a Korean statute,
    enforcement decree, or enforcement rule by law name.

    검색 결과에는 법령명, 법령ID, 법령일련번호(MST),
    시행일자, 공포일자, 소관부처 등이 포함됩니다.
    """

    return await search_law_api(
        query=query,
        page=page,
        num_of_rows=num_of_rows,
    )


@mcp.tool
async def get_law(
    mst: str | None = None,
    law_id: str | None = None,
) -> dict[str, Any]:
    """
    국가법령정보센터에서 현행 법령 전체 본문을 조회합니다.

    Use this when the full text of a law is needed.
    search_law 결과의 MST 또는 법령ID를 사용합니다.

    가능한 경우 MST 사용을 권장합니다.
    """

    return await get_law_api(
        mst=mst,
        law_id=law_id,
    )


@mcp.tool
async def get_article(
    law_id: str,
    article: int,
    article_sub: int | None = None,
    paragraph: int | None = None,
    item: int | None = None,
    mok: str | None = None,
) -> dict[str, Any]:
    """
    법령의 특정 조·항·호·목을 조회합니다.

    Use this when the user identifies or needs a specific
    article, paragraph, item, or sub-item of a Korean law.

    예:
    제22조:
      article=22

    제22조의2:
      article=22
      article_sub=2

    제22조제1항:
      article=22
      paragraph=1

    제22조제1항제2호:
      article=22
      paragraph=1
      item=2
    """

    return await get_article_api(
        law_id=law_id,
        article=article,
        article_sub=article_sub,
        paragraph=paragraph,
        item=item,
        mok=mok,
    )


@mcp.tool
async def search_law_text(
    query: str,
    keyword: str,
) -> dict[str, Any]:
    """
    법령명을 검색한 뒤 검색된 법령의 전체 본문에서
    특정 키워드가 포함되어 있는지 확인합니다.

    Use this when the user asks which related laws contain
    a particular legal term or phrase.
    """

    search_data = await search_law_api(
        query=query,
        page=1,
        num_of_rows=20,
    )

    law_search = search_data.get("LawSearch", {})
    laws = law_search.get("law", [])

    if isinstance(laws, dict):
        laws = [laws]

    matches: list[dict[str, Any]] = []

    for law in laws:
        mst = law.get("법령일련번호")

        if not mst:
            continue

        body = await get_law_api(
            mst=str(mst),
        )

        body_text = str(body)

        if keyword in body_text:
            matches.append(
                {
                    "법령명": law.get("법령명한글"),
                    "법령ID": law.get("법령ID"),
                    "MST": mst,
                    "keyword": keyword,
                    "본문전체": body,
                }
            )

    return {
        "query": query,
        "keyword": keyword,
        "match_count": len(matches),
        "matches": matches,
    }


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "8000"))

    mcp.run(
        transport="http",
        host="0.0.0.0",
        port=port,
    )