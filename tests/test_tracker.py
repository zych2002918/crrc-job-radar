"""增量追踪模块测试。"""

from crrc_radar import tracker


def test_load_snapshot_missing_file(tmp_path):
    assert tracker.load_snapshot(tmp_path / "nope.json") == set()


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "snap.json"
    posts = [{"postId": "a1"}, {"postId": "b2"}, {"postId": None}]
    tracker.save_snapshot(posts, path)
    assert tracker.load_snapshot(path) == {"a1", "b2"}


def test_diff_new_posts(tmp_path):
    path = tmp_path / "snap.json"
    old = [{"postId": "a1"}, {"postId": "b2"}]
    tracker.save_snapshot(old, path)
    current = [{"postId": "a1"}, {"postId": "b2"}, {"postId": "c3"}]
    new = tracker.diff_new_posts(current, tracker.load_snapshot(path))
    assert [p["postId"] for p in new] == ["c3"]


def test_diff_empty_history():
    posts = [{"postId": "a1"}]
    assert len(tracker.diff_new_posts(posts, set())) == 1


def test_mark_new_flags_only_new():
    marked = tracker.mark_new([{"postId": "a1"}, {"postId": "c3"}], {"c3"})
    assert marked[0].get("is_new") is None
    assert marked[1]["is_new"] is True


def test_load_snapshot_ignores_corrupt(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")
    assert tracker.load_snapshot(path) == set()