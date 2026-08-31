"""岗位筛选器：按关键词匹配岗位字段，产出命中分析。"""

from collections import Counter

# 默认筛选维度：方向关键词 + 目标地点
DEFAULT_KEYWORDS = {
    "测试": ("测试", "测开", "QA", "质量"),
    "软件/嵌入式": ("软件", "嵌入式", "网络", "开发", "程序"),
    "电子信息": ("电子", "通信", "控制", "信息"),
    "自动化": ("自动化",),
}

TARGET_CITIES = ("大连", "沈阳", "长春", "北京")


def _contains(text: str | None, keywords: tuple[str, ...]) -> bool:
    if not text:
        return False
    return any(k.lower() in text.lower() for k in keywords)


def match_post(post: dict, keywords: dict[str, tuple[str, ...]] | None = None) -> set[str]:
    """返回该岗位命中的维度集合（空集=未命中）。"""
    keywords = keywords or DEFAULT_KEYWORDS
    fields = " ".join(filter(None, (
        post.get("postName"),
        post.get("subject"),
        post.get("company"),
        post.get("workPlaceStr"),
    )))
    return {dim for dim, kws in keywords.items() if _contains(fields, kws)}


def filter_posts(
    posts: list[dict],
    keywords: dict[str, tuple[str, ...]] | None = None,
    target_cities: tuple[str, ...] = TARGET_CITIES,
) -> dict:
    """筛选岗位并统计。

    返回:
        matched:  至少命中一个方向维度的岗位列表（附 hits 字段）
        by_city:  按目标城市命中的岗位
        stats:    总岗位数 / 命中数 / 维度分布 / 公司分布
    """
    keywords = keywords or DEFAULT_KEYWORDS
    matched = []
    by_city: dict[str, list[dict]] = {c: [] for c in target_cities}
    for post in posts:
        hits = match_post(post, keywords)
        if hits:
            post = dict(post)
            post["hits"] = sorted(hits)
            matched.append(post)
        place = post.get("workPlaceStr") or ""
        for city in target_cities:
            if city in place and post not in by_city[city]:
                by_city[city].append(post)

    dim_dist = Counter(h for p in matched for h in p["hits"])
    company_dist = Counter(p.get("company") or "未知" for p in matched)
    return {
        "matched": matched,
        "by_city": by_city,
        "stats": {
            "total": len(posts),
            "matched": len(matched),
            "dim_dist": dict(dim_dist),
            "company_dist": dict(company_dist),
        },
    }