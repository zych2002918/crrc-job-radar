"""岗位增量追踪：快照对比，识别新发布岗位。

每次抓取后保存快照（postId 集合 + 时间戳），下次抓取时对比，
标记新增岗位——用于定时追踪"今天中车新放了哪些岗位"。
"""

import json
import time
from pathlib import Path

DEFAULT_SNAPSHOT = "snapshot.json"


def load_snapshot(path: str | Path = DEFAULT_SNAPSHOT) -> set[str]:
    """加载历史快照中的 postId 集合（文件不存在则返回空集）。"""
    p = Path(path)
    if not p.exists():
        return set()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return set(data.get("post_ids", []))
    except (json.JSONDecodeError, OSError):
        return set()


def save_snapshot(posts: list[dict], path: str | Path = DEFAULT_SNAPSHOT) -> None:
    """保存当前岗位快照（postId 集合 + 抓取时间）。"""
    data = {
        "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "count": len(posts),
        "post_ids": [p.get("postId") for p in posts if p.get("postId")],
    }
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def diff_new_posts(posts: list[dict], old_ids: set[str]) -> list[dict]:
    """返回本次抓取中新增的岗位（postId 不在历史快照中）。"""
    return [p for p in posts if p.get("postId") and p.get("postId") not in old_ids]


def mark_new(posts: list[dict], new_ids: set[str]) -> list[dict]:
    """给新增岗位打上 NEW 标记（用于报告展示）。"""
    out = []
    for p in posts:
        p = dict(p)
        if p.get("postId") in new_ids:
            p["is_new"] = True
        out.append(p)
    return out