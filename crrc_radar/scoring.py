"""岗位-简历匹配打分：把个人技能档案与岗位要求比对，输出推荐投递排序。

个人档案（JSON）字段:
    name           候选人姓名
    target_roles   目标岗位关键词（命中直接加权）
    skills         技能关键词列表（出现在岗位文本中即计分）
    weights        方向加权（可选，默认 {测试:3, 软件:2, 嵌入式:2, 电子:2}）

打分逻辑:
    目标岗位命中  +30（如"测试"类岗位）
    技能命中      +4/项（上限 +40）
    方向权重命中  +权重（默认 测试+15 / 软件+10 / 嵌入式+10 / 电子+5）
    总分上限 100
"""

import json
from pathlib import Path

DEFAULT_WEIGHTS = {"测试": 15, "软件": 10, "嵌入式": 10, "电子": 5, "自动化": 5}


def load_profile(path: str | Path) -> dict:
    """加载个人技能档案。"""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"档案文件不存在: {path}")
    data = json.loads(p.read_text(encoding="utf-8"))
    data.setdefault("skills", [])
    data.setdefault("target_roles", [])
    data.setdefault("weights", DEFAULT_WEIGHTS)
    return data


def _post_text(post: dict) -> str:
    return " ".join(filter(None, (
        post.get("postName"),
        post.get("subject"),
        post.get("company"),
    )))


def score_post(post: dict, profile: dict) -> dict:
    """计算单个岗位的匹配得分。"""
    text = _post_text(post)
    score = 0
    reasons = []

    # 1) 目标岗位命中
    target_hit = [t for t in profile.get("target_roles", []) if t.lower() in text.lower()]
    if target_hit:
        score += 30
        reasons.append(f"目标岗位:{'/'.join(target_hit)}")

    # 2) 技能命中
    matched_skills = [s for s in profile.get("skills", []) if s.lower() in text.lower()]
    if matched_skills:
        score += min(4 * len(matched_skills), 40)
        reasons.append(f"技能:{len(matched_skills)}项")

    # 3) 方向加权
    for dim, weight in profile.get("weights", DEFAULT_WEIGHTS).items():
        if dim in text:
            score += weight
            reasons.append(f"{dim}+{weight}")

    return {
        "score": min(score, 100),
        "matched_skills": matched_skills,
        "target_roles_hit": target_hit,
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