"""投递清单（markdown）生成。"""

from datetime import datetime


def post_url(post: dict) -> str:
    """构造岗位详情页链接（中车招聘云平台岗位详情）。"""
    suite = post.get("currentSuiteKey") or ""
    post_id = post.get("postId") or ""
    return f"https://crrc.hotjob.cn/{suite}/pb/posDetail.html?postId={post_id}"


def _row(post: dict) -> str:
    cells = [
        (post.get("company") or "").replace("|", "\\|"),
        (post.get("postName") or "").replace("|", "\\|"),
        (post.get("workPlaceStr") or "").replace("|", "\\|"),
        (post.get("educationStr") or "").replace("|", "\\|"),
        (post.get("endDate") or "—").split(" ")[0],
        (post.get("projectName") or "").replace("|", "\\|"),
        (post.get("postCode") or ""),
        ",".join(post.get("hits", [])),
        post_url(post),
    ]
    return "| " + " | ".join(cells) + " |"


def build_report(result: dict, source_note: str = "") -> str:
    """生成 markdown 投递清单。"""
    stats = result["stats"]
    lines = [
        "# 中车校招岗位投递清单（自动筛选）",
        "",
        f"> 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> 统计：共 {stats['total']} 个在招岗位，命中筛选 {stats['matched']} 个",
        f"> {source_note}",
        "",
        "## 一、命中岗位清单",
        "",
        "| 公司 | 岗位 | 地点 | 学历 | 截止日期 | 项目 | 岗位编码 | 命中维度 | 详情 |",
        "|------|------|------|------|----------|------|----------|----------|------|",
    ]
    lines += [_row(p) for p in result["matched"]]

    lines += ["", "## 二、按目标城市", ""]
    for city, posts in result["by_city"].items():
        lines += [f"### {city}（{len(posts)} 个）", ""]
        lines += [f"- {p.get('company')}｜{p.get('postName')}（{p.get('educationStr')}）" for p in posts]
        lines += [""]

    lines += [
        "## 三、维度命中分布", "",
        "| 维度 | 命中数 |", "|------|--------|",
    ]
    for dim, n in sorted(stats["dim_dist"].items(), key=lambda x: -x[1]):
        lines.append(f"| {dim} | {n} |")

    lines += ["", "## 四、命中岗位公司分布", ""]
    for company, n in sorted(stats["company_dist"].items(), key=lambda x: -x[1]):
        lines.append(f"- {company}：{n} 个")
    return "\n".join(lines) + "\n"