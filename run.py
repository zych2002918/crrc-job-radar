"""crrc-job-radar CLI：抓取中车校招岗位 → 关键词筛选 → 生成投递清单。

用法:
    python run.py                          # 抓全量并生成 jobs.md
    python run.py --work-place 0/4/77      # 只抓辽宁省（大连）岗位
    python run.py --out my-jobs.md         # 自定义输出文件
    python run.py --max-pages 10           # 限制抓取页数
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from crrc_radar import api, filters, report, tracker

DEFAULT_OUT = "jobs.md"


def main() -> int:
    parser = argparse.ArgumentParser(description="中车校招岗位雷达")
    parser.add_argument("--work-place", default="", help="工作地点代码，如 0/4/77（辽宁省）")
    parser.add_argument("--max-pages", type=int, default=200, help="最大抓取页数")
    parser.add_argument("--out", default=DEFAULT_OUT, help="输出 markdown 文件")
    parser.add_argument("--recruit-type", type=int, default=1, help="1=校招")
    parser.add_argument("--track", action="store_true",
                        help="启用增量追踪：对比上次快照，标注新增岗位")
    parser.add_argument("--snapshot", default=tracker.DEFAULT_SNAPSHOT, help="快照文件路径")
    args = parser.parse_args()

    print(f"[1/3] 抓取中车校招岗位（work_place={args.work_place or '全部'}）...")
    posts = api.fetch_all(
        work_place_code=args.work_place,
        recruit_type=args.recruit_type,
        max_pages=args.max_pages,
    )
    print(f"      共 {len(posts)} 个岗位")

    print("[2/3] 关键词筛选（测试/软件/电子/自动化/目标城市）...")
    result = filters.filter_posts(posts)
    s = result["stats"]
    print(f"      命中 {s['matched']}/{s['total']}，维度分布：{s['dim_dist']}")

    if args.track:
        old_ids = tracker.load_snapshot(args.snapshot)
        new_posts = tracker.diff_new_posts(posts, old_ids)
        result["matched"] = tracker.mark_new(result["matched"], {p["postId"] for p in new_posts})
        print(f"      增量追踪：新增 {len(new_posts)} 个岗位（对比 {len(old_ids)} 条历史快照）")
        tracker.save_snapshot(posts, args.snapshot)

    print(f"[3/3] 生成投递清单 -> {args.out}")
    md = report.build_report(
        result,
        source_note=f"数据源：中车招聘云平台公开 API（suite={api.SUITE_ID}）",
    )
    Path(args.out).write_text(md, encoding="utf-8")
    print("完成。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())