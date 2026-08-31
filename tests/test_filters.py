"""筛选器与报告生成的单元测试（离线可跑，不依赖网络）。"""

from crrc_radar import filters, report

SAMPLE = [
    {
        "postName": "软件测试工程师",
        "company": "中车大连机车车辆有限公司",
        "workPlaceStr": "大连市",
        "educationStr": "硕士",
        "subject": "计算机科学与技术、软件工程",
        "endDate": "2026-09-30 00:00:00",
        "postCode": "CRRC0001",
        "postId": "abc123",
        "currentSuiteKey": "SU64d47c466202cc36e27a52d4",
        "projectName": "2027届校园招聘",
    },
    {
        "postName": "机械设计师",
        "company": "中车大连机车车辆有限公司",
        "workPlaceStr": "大连市",
        "educationStr": "硕士",
        "subject": "车辆工程、机械工程",
        "endDate": "2026-09-30 00:00:00",
        "postCode": "CRRC0002",
        "postId": "abc456",
        "currentSuiteKey": "SU64d47c466202cc36e27a52d4",
        "projectName": "2027届校园招聘",
    },
]


def test_filter_matches_test_keyword():
    result = filters.filter_posts(SAMPLE)
    assert result["stats"]["total"] == 2
    assert result["stats"]["matched"] == 1
    assert result["matched"][0]["postName"] == "软件测试工程师"
    assert "测试" in result["matched"][0]["hits"]


def test_city_filter_dalian():
    result = filters.filter_posts(SAMPLE)
    assert len(result["by_city"]["大连"]) == 2


def test_city_filter_beijing_empty():
    result = filters.filter_posts(SAMPLE)
    assert result["by_city"]["北京"] == []


def test_custom_keywords():
    result = filters.filter_posts(SAMPLE, keywords={"机械": ("机械设计", "机械工程")})
    assert result["stats"]["matched"] == 1
    assert result["matched"][0]["postName"] == "机械设计师"


def test_match_post_empty_text():
    assert filters.match_post({"postName": None, "subject": None}) == set()


def test_report_contains_table():
    result = filters.filter_posts(SAMPLE)
    md = report.build_report(result)
    assert "软件测试工程师" in md
    assert "| 公司 | 岗位 |" in md
    assert "中车大连机车车辆有限公司" in md


def test_post_url_construction():
    url = report.post_url(SAMPLE[0])
    assert url == "https://crrc.hotjob.cn/SU64d47c466202cc36e27a52d4/pb/posDetail.html?postId=abc123"