"""多维匹配打分测试：岗位方向/学历/院校/生源地点/届次/专业/技能项目。"""

import pytest

from crrc_radar import scoring

PROFILE = {
    "name": "测试",
    "education": "硕士",
    "graduation_year": "2027届",
    "school": "大连交通大学",
    "school_tier": "轨道交通行业特色高校",
    "school_bonus": 8,
    "major": "电子信息",
    "major_keywords": ["电子", "信息", "通信", "控制", "计算机"],
    "hometown_province": "辽宁",
    "hometown_cities": ["大连", "沈阳"],
    "work_cities": ["大连", "上海"],
    "target_roles": ["软件测试工程师", "测试"],
    "skills": ["Python", "pytest", "测试", "CAN"],
    "project_keywords": ["CAN", "TCMS", "自动化测试"],
}

POST_GOOD = {
    "postName": "软件测试工程师",
    "company": "中车大连机车车辆有限公司",
    "workPlaceStr": "大连市",
    "educationStr": "硕士研究生及以上",
    "subject": "计算机科学与技术、软件工程、电子信息、网络控制、CAN总线",
    "projectName": "2027届校园招聘",
    "postId": "p1",
}
POST_FAR = {
    "postName": "机械设计师",
    "company": "中车株洲电力机车有限公司",
    "workPlaceStr": "株洲市",
    "educationStr": "博士研究生",
    "subject": "车辆工程、机械工程",
    "projectName": "2027届校园招聘",
    "postId": "p2",
}


def test_load_profile_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        scoring.load_profile(tmp_path / "nope.json")


def test_load_profile_defaults(tmp_path):
    path = tmp_path / "p.json"
    path.write_text('{"name":"x"}', encoding="utf-8")
    profile = scoring.load_profile(path)
    assert profile["skills"] == []
    assert profile["school_bonus"] == 0


# ---- 维度分项 ----

def test_dimension_direction():
    sub, reason = scoring._score_direction(POST_GOOD, PROFILE)
    assert sub == 25
    assert "软件测试工程师" in reason


def test_dimension_education_match():
    sub, _ = scoring._score_education(POST_GOOD, PROFILE)
    assert sub == 15


def test_dimension_education_doctor_mismatch():
    sub, reason = scoring._score_education(POST_FAR, PROFILE)
    assert sub == 0
    assert "不匹配" in reason


def test_dimension_school_bonus_crrc():
    sub, _ = scoring._score_school(POST_GOOD, PROFILE)
    assert sub == 8  # 中车系 + 行业特色高校加成


def test_dimension_school_no_bonus_non_crrc():
    post = dict(POST_GOOD, company="某软件公司")
    sub, _ = scoring._score_school(post, PROFILE)
    assert sub == 0


def test_dimension_location_hometown_and_city():
    sub, reason = scoring._score_location(POST_GOOD, PROFILE)
    assert sub == 15  # 生源省内城市 + 可工作城市
    assert "大连" in reason


def test_dimension_location_miss():
    sub, _ = scoring._score_location(POST_FAR, PROFILE)
    assert sub == 0


def test_dimension_graduation_match():
    sub, _ = scoring._score_graduation(POST_GOOD, PROFILE)
    assert sub == 10


def test_dimension_graduation_mismatch():
    post = dict(POST_GOOD, projectName="2026届校园招聘")
    sub, reason = scoring._score_graduation(post, PROFILE)
    assert sub == 2
    assert "2026届" in reason


def test_dimension_major_hit():
    sub, reason = scoring._score_major(POST_GOOD, PROFILE)
    assert sub >= 7
    assert "命中" in reason


def test_dimension_major_miss():
    sub, _ = scoring._score_major(POST_FAR, PROFILE)
    assert sub <= 5


def test_dimension_skills_projects():
    sub, reason = scoring._score_skills_projects(POST_GOOD, PROFILE)
    assert sub >= 5
    assert "技能" in reason


# ---- 综合 ----

def test_score_good_post_high():
    detail = scoring.score_post(POST_GOOD, PROFILE)
    assert detail["score"] >= 60
    assert detail["dimensions"]["岗位方向"] == 25
    assert detail["dimensions"]["学历"] == 15


def test_score_far_post_low():
    detail = scoring.score_post(POST_FAR, PROFILE)
    assert detail["score"] < 40


def test_rank_orders_by_score():
    posts = [POST_FAR, POST_GOOD]
    ranked = scoring.rank_posts(posts, PROFILE, top=5)
    assert ranked[0]["postId"] == "p1"
    scores = [p["score"] for p in ranked]
    assert scores == sorted(scores, reverse=True)


def test_rank_respects_top():
    posts = [POST_GOOD, dict(POST_GOOD, postId="p3"), dict(POST_GOOD, postId="p4")]
    ranked = scoring.rank_posts(posts, PROFILE, top=2)
    assert len(ranked) == 2


def test_score_capped_at_100():
    profile = dict(PROFILE, skills=["Python", "pytest", "测试", "CAN", "自动化", "Linux", "Git", "SQL"])
    detail = scoring.score_post(POST_GOOD, profile)
    assert detail["score"] <= 100