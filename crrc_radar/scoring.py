"""岗位-简历匹配打分：招聘方视角的多维匹配。

个人档案（JSON）字段:
    name               候选人姓名
    education          学历（本科/硕士/博士）
    graduation_year    毕业届次（如 "2027届"）
    school             毕业院校
    school_tier        院校层次（985/211/双一流/行业特色高校）
    school_bonus       院校在目标行业的认可度加成（0-10）
    major              专业
    major_keywords     专业相关关键词（匹配岗位专业要求）
    hometown_province  籍贯省份（央企校招关注生源地稳定性）
    work_cities        可工作城市列表
    target_roles       目标岗位关键词
    skills             技能关键词
    project_keywords   项目/经历关键词（项目贴合度）

打分维度（满分 100）:
    岗位方向 25 / 学历 15 / 院校 10 / 生源与地点 15 / 届次 10 / 专业 10 / 技能与项目 15
"""

import json
from pathlib import Path

DIMENSIONS = {
    "岗位方向": 25,
    "学历": 15,
    "院校": 10,
    "生源与地点": 15,
    "届次": 10,
    "专业": 10,
    "技能与项目": 15,
}


def load_profile(path: str | Path) -> dict:
    """加载个人档案。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"档案文件不存在: {path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    defaults = {
        "education": "", "graduation_year": "", "school": "", "school_tier": "",
        "school_bonus": 0, "major": "", "major_keywords": [],
        "hometown_province": "", "work_cities": [], "target_roles": [],
        "skills": [], "project_keywords": [],
    }
    for k, v in defaults.items():
        data.setdefault(k, v)
    return data


def _text(post: dict) -> str:
    return " ".join(filter(None, (
        post.get("postName"), post.get("subject"),
        post.get("company"), post.get("workPlaceStr"),
    )))


def _score_direction(post: dict, profile: dict) -> tuple[int, str]:
    """岗位方向（25）：目标岗位命中。"""
    text = _text(post)
    hit = [t for t in profile["target_roles"] if t.lower() in text.lower()]
    if hit:
        return 25, f"目标岗位:{'/'.join(hit[:2])}"
    return 0, "方向未命中"


def _score_education(post: dict, profile: dict) -> tuple[int, str]:
    """学历（15）：岗位学历要求 vs 候选人学历。"""
    req = (post.get("educationStr") or "").replace(" ", "")
    cand = profile["education"]
    if not req or not cand:
        return 10, "学历:信息不足"
    if cand in req:  # "硕士研究生" in "硕士研究生及以上" / "硕士研究生"
        return 15, f"学历:匹配({req})"
    if "博士" in req and "博士" not in cand:
        return 0, f"学历:要求{req}，不匹配"
    if "硕士" in req and cand == "博士":
        return 13, f"学历:博士优于{req}"
    if cand in ("硕士", "博士") and "本科" in req:
        return 15, f"学历:兼容({cand}满足{req})"
    return 5, f"学历:待确认({req})"


def _score_school(post: dict, profile: dict) -> tuple[int, str]:
    """院校（10）：行业特色院校在中车系公司的认可度加成。"""
    company = post.get("company") or ""
    if "中车" not in company:
        return 0, "非中车系，无院校加成"
    bonus = min(int(profile.get("school_bonus", 0)), 10)
    if bonus <= 0:
        return 0, "院校加成未配置"
    return bonus, f"{profile.get('school', '')}({profile.get('school_tier', '')})+{bonus}"


def _score_location(post: dict, profile: dict) -> tuple[int, str]:
    """生源与地点（15）：籍贯省份就近 + 可工作城市命中。"""
    place = post.get("workPlaceStr") or ""
    score = 0
    reasons = []
    hometown = profile.get("hometown_province", "")
    if hometown and hometown in place:
        score += 8
        reasons.append(f"生源省份:{hometown}")
    hometown_cities = [c for c in profile.get("hometown_cities", []) if c in place]
    if hometown_cities:
        score += 8
        reasons.append(f"生源省内城市:{'/'.join(hometown_cities)}")
    cities = [c for c in profile.get("work_cities", []) if c in place]
    if cities:
        score += 7
        reasons.append(f"可工作城市:{'/'.join(cities)}")
    if not reasons:
        return 0, "地点未命中"
    return score, ";".join(reasons)


def _score_graduation(post: dict, profile: dict) -> tuple[int, str]:
    """届次（10）：岗位面向的毕业届次 vs 候选人届次。"""
    project = post.get("projectName") or ""
    year = profile.get("graduation_year", "")
    if not year or not project:
        return 5, "届次:信息不足"
    if year in project:
        return 10, f"届次:匹配({year})"
    # 岗位未标注届次（如长期岗位）
    if "届" not in project:
        return 8, "届次:未标注"
    return 2, f"届次:面向{project}，候选人{year}"


def _score_major(post: dict, profile: dict) -> tuple[int, str]:
    """专业（10）：岗位专业要求与候选人专业关键词命中率。"""
    subject = post.get("subject") or ""
    keywords = profile.get("major_keywords", [])
    if not keywords or not subject:
        return 5, "专业:信息不足"
    hit = [k for k in keywords if k in subject]
    if not hit:
        return 2, "专业:未命中要求"
    ratio = len(hit) / len(keywords)
    score = 5 + round(5 * min(ratio, 1.0))
    return score, f"专业:命中{len(hit)}个关键词"


def _score_skills_projects(post: dict, profile: dict) -> tuple[int, str]:
    """技能与项目（15）：技能命中（封顶 10）+ 项目贴合（封顶 5）。"""
    text = _text(post)
    skills = [s for s in profile.get("skills", []) if s.lower() in text.lower()]
    projects = [p for p in profile.get("project_keywords", []) if p.lower() in text.lower()]
    score = min(2 * len(skills), 10) + min(len(projects), 5)
    reasons = []
    if skills:
        reasons.append(f"技能:{len(skills)}项")
    if projects:
        reasons.append(f"项目贴合:{'/'.join(projects[:3])}")
    return score, ";".join(reasons)


SCORERS = {
    "岗位方向": _score_direction,
    "学历": _score_education,
    "院校": _score_school,
    "生源与地点": _score_location,
    "届次": _score_graduation,
    "专业": _score_major,
    "技能与项目": _score_skills_projects,
}


def score_post(post: dict, profile: dict) -> dict:
    """计算单个岗位的匹配得分（满分 100）。"""
    total = 0
    dims = {}
    reasons = []
    for dim in DIMENSIONS:
        weight = DIMENSIONS[dim]
        sub, reason = SCORERS[dim](post, profile)
        dims[dim] = sub
        total += sub
        if reason:
            reasons.append(reason)
    return {
        "score": min(total, 100),
        "dimensions": dims,
        "matched_skills": [
            s for s in profile.get("skills", [])
            if s.lower() in _text(post).lower()
        ],
        "reasons": reasons,
    }


def rank_posts(posts: list[dict], profile: dict, top: int = 10) -> list[dict]:
    """按匹配分排序，返回 TopN（带打分明细）。"""
    ranked = []
    for post in posts:
        detail = score_post(post, profile)
        if detail["score"] > 0:
            ranked.append((detail["score"], post, detail))
    ranked.sort(key=lambda x: -x[0])
    return [
        {"score": sc, **post, "match": detail}
        for sc, post, detail in ranked[:top]
    ]