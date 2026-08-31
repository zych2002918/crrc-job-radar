"""岗位-简历匹配打分模块测试。"""

import pytest

from crrc_radar import scoring

PROFILE = {
    "name": "测试",
    "target_roles": ["软件测试工程师", "测试"],
    "skills": ["Python", "pytest", "SQL", "Jira", "嵌入式", "CAN", "测试"],
    "weights": {"测试": 15, "软件": 10, "嵌入式": 10, "电子": 5},
}

POST_TEST = {
    "postName": "软件测试工程师",
    "company": "中车长春轨道客车",
    "workPlaceStr": "长春市",
    "subject": "计算机科学与技术、软件工程、Python",
    "postId": "p1",
}
POST_MECH = {
    "postName": "机械设计师",
    "company": "中车大连机车",
    "workPlaceStr": "大连市",
    "subject": "车辆工程、机械工程",
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
    assert profile["weights"] == scoring.DEFAULT_WEIGHTS


def test_score_target_role_hit():
    detail = scoring.score_post(POST_TEST, PROFILE)
    assert "软件测试工程师" in detail["target_roles_hit"]
    assert detail["score"] >= 30


def test_score_skills_matched():
    detail = scoring.score_post(POST_TEST, PROFILE)
    assert "Python" in detail["matched_skills"]
    assert detail["score"] >= 30 + 4


def test_score_non_matching_post():
    detail = scoring.score_post(POST_MECH, PROFILE)
    assert detail["score"] == 0


def test_rank_orders_by_score():
    posts = [
        dict(POST_TEST, postId="p1", postName="软件测试工程师"),
        dict(POST_TEST, postId="p2", postName="嵌入式软件工程师"),
        dict(POST_TEST, postId="p3", postName="机械设计师"),
    ]
    ranked = scoring.rank_posts(posts, PROFILE, top=5)
    scores = [p["score"] for p in ranked]
    assert scores == sorted(scores, reverse=True)
    assert ranked[0]["postId"] == "p1"


def test_rank_respects_top():
    posts = [POST_TEST, dict(POST_TEST, postId="p3"), dict(POST_TEST, postId="p4")]
    ranked = scoring.rank_posts(posts, PROFILE, top=2)
    assert len(ranked) == 2


def test_rank_excludes_zero_score():
    ranked = scoring.rank_posts([POST_MECH], PROFILE, top=5)
    assert ranked == []


def test_score_capped_at_100():
    profile = dict(PROFILE, skills=["测试", "Python", "pytest", "SQL", "Jira", "CAN", "嵌入式", "软件", "Linux", "Git", "质量", "自动化"])
    detail = scoring.score_post(POST_TEST, profile)
    assert detail["score"] <= 100