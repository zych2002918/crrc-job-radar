"""中车招聘云平台公开 API 封装（零第三方依赖，标准库 urllib）。

平台: https://crrc.hotjob.cn
接口: POST /wecruit/positionInfo/listPosition/{suite_id}
      ?iSaJAx=isAjax&request_locale=zh_CN&t={ms_timestamp}
      body: isFrompb=true&recruitType=1&pageSize=12&currentPage=N[&workPlaceCode=...]
返回: {"data": {"pageForm": {"totalPage": N, "pageData": [...]}}}
"""

import json
import time
import urllib.parse
import urllib.request

BASE_URL = "https://crrc.hotjob.cn/wecruit/positionInfo/listPosition"
# 中车招聘云平台门户 suite（聚合多家子公司岗位）
SUITE_ID = "SU64d47c466202cc36e27a52d4"
DEFAULT_PAGE_SIZE = 12

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://crrc.hotjob.cn/",
    "Content-Type": "application/x-www-form-urlencoded",
}

# 保留字段（前端展示/投递所需的最小集合）
KEEP_FIELDS = (
    "postName", "company", "workPlaceStr", "educationStr", "subject",
    "endDate", "publishDate", "postCode", "postId", "projectName",
    "currentSuiteKey", "recruitNumStr", "pageViews",
)


def _request(url: str, body: str, timeout: float = 20.0) -> dict:
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=HEADERS, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _pick(raw: dict) -> dict:
    return {k: raw.get(k) for k in KEEP_FIELDS}


def fetch_page(
    suite_id: str = SUITE_ID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    work_place_code: str = "",
    recruit_type: int = 1,
    timeout: float = 30.0,
    retries: int = 3,
) -> tuple[list[dict], int]:
    """抓取一页岗位，返回 (岗位列表, 总页数)。带重试。"""
    params = urllib.parse.urlencode({
        "iSaJAx": "isAjax",
        "request_locale": "zh_CN",
        "t": int(time.time() * 1000),
    })
    body = urllib.parse.urlencode({
        "isFrompb": "true",
        "recruitType": recruit_type,
        "pageSize": page_size,
        "currentPage": page,
        **({"workPlaceCode": work_place_code} if work_place_code else {}),
    })
    url = f"{BASE_URL}/{suite_id}?{params}"
    for attempt in range(retries):
        try:
            data = _request(url, body, timeout=timeout)
            break
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    page_form = (data.get("data") or {}).get("pageForm") or {}
    total_pages = int(page_form.get("totalPage") or 0)
    posts = [_pick(p) for p in (page_form.get("pageData") or [])]
    return posts, total_pages


def fetch_all(
    suite_id: str = SUITE_ID,
    work_place_code: str = "",
    recruit_type: int = 1,
    max_pages: int = 200,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: float = 20.0,
) -> list[dict]:
    """抓取全部岗位（自动分页）。"""
    posts: list[dict] = []
    page = 1
    while page <= max_pages:
        batch, total_pages = fetch_page(
            suite_id, page, page_size, work_place_code, recruit_type, timeout
        )
        posts.extend(batch)
        if page >= total_pages or not batch:
            break
        page += 1
        time.sleep(0.3)  # 礼貌性限速
    return posts