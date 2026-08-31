# CRRC Job Radar — 中车校招岗位雷达

[![Daily Scan](https://github.com/zych2002918/crrc-job-radar/actions/workflows/daily.yml/badge.svg)](https://github.com/zych2002918/crrc-job-radar/actions)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![tests: 32](https://img.shields.io/badge/tests-32%20passed-brightgreen)](#)

针对中国中车集团（含中车大连机车车辆等子公司）校园招聘的岗位情报工具：
调用**中车招聘云平台公开 API** 抓取在招岗位，按方向关键词（测试 / 软件嵌入式 / 电子信息 / 自动化）
与目标城市（大连 / 沈阳 / 长春 / 北京）自动筛选，生成 markdown 投递清单。

纯 Python 标准库实现，**零第三方依赖**，无需登录即可运行。

> 📊 **每日自动更新**：仓库的 [docs/jobs.md](docs/jobs.md) 由 GitHub Actions 每天自动抓取生成，
> 新增岗位带 🆕 标记——想看"中车今天新放了什么岗位"，直接看这个文件。

```
中车招聘云平台 API ──▶ 抓取全量在招岗位（自动分页 + 重试）
        │
        ▼
关键词筛选（测试/软件/电子/自动化 × 目标城市）
        │
        ▼
增量追踪（对比快照，标出 🆕 新增岗位）
        │
        ▼
markdown 投递清单（公司/岗位/地点/学历/截止/详情链接 + 统计）
```

## 快速开始

```bash
python run.py                  # 抓全量校招岗位 -> jobs.md
python run.py --work-place 0/4/77   # 只看辽宁省（大连）岗位
python run.py --track          # 增量追踪：对比上次快照，标出新增岗位
python run.py --profile profile.example.json --top 10   # 岗位-简历匹配打分，输出推荐 Top10
python run.py --out my.md --max-pages 50
```

## 个人匹配打分（--profile）

以**招聘方视角**做多维匹配打分（满分 100），报告顶部输出
"个人匹配推荐 TopN"（排名/匹配分/命中原因明细）：

| 维度 | 分值 | 说明 |
|------|------|------|
| 岗位方向 | 25 | 目标岗位关键词命中 |
| 学历 | 15 | 岗位学历要求 vs 候选人学历（博士要求不匹配会大幅减分） |
| 院校 | 10 | 行业特色院校在中车系公司的认可度加成（可配置） |
| 生源与地点 | 15 | 籍贯省份 / 生源省内城市 / 可工作城市与岗位地点匹配（央企关注生源稳定性） |
| 届次 | 10 | 岗位面向的毕业届次 vs 候选人届次（如"面向2026届"会提示） |
| 专业 | 10 | 岗位专业要求与候选人专业关键词命中率 |
| 技能与项目 | 15 | 技能关键词 + 项目经历关键词（TCMS/CAN/自动化测试等）贴合度 |

```
| 1 | 中车大连电力牵引研发中心 | 嵌入式开发设计师 | 75/100 | 目标岗位:嵌入式;学历:匹配;院校:大连交通大学+8;生源省内城市:大连;可工作城市:大连;届次:面向2026届，候选人2027届;专业:命中3关键词;项目贴合:嵌入式 |
| 2 | 中车长春轨道客车 | 软件测试工程师 | 72/100 | 目标岗位:软件测试工程师;学历:兼容;院校+8;可工作城市:长春;届次:匹配(2027届);... |
```

技能档案示例（`profile.example.json`）：学历 / 毕业届次 / 院校层次与加成 /
籍贯省份与省内城市 / 可工作城市 / 目标岗位 / 技能 / 项目关键词，
按你的实际简历修改后使用。

## 输出示例

生成的 `jobs.md` 包含：

- **命中岗位清单**：公司 / 岗位 / 地点 / 学历 / 截止日期 / 项目 / 岗位编码 / 命中维度 / 详情链接（🆕 = 本次新增）
- **按目标城市分组**：大连 / 沈阳 / 长春 / 北京各有哪些岗位
- **维度命中分布**：测试、软件/嵌入式、电子信息、自动化各命中多少
- **公司分布**：命中岗位按公司统计

实际运行效果（2026-08-31）：全量 **417 个在招岗位**，筛选命中 **122 个**
（含"软件测试工程师""网络安全工程师""网络控制及人机交互工程师"等对口岗位）。

## 定时任务（可选）

仓库自带 GitHub Actions 每日自动扫描（`.github/workflows/daily.yml`）：
每天北京时间 08:00 自动抓取 → 更新 `docs/jobs.md` → 提交推送。

启用方法：
1. GitHub 仓库 → **Settings → Secrets and variables → Actions → New repository secret**
2. 名称填 `CRRCR_TOKEN`，值填你的 GitHub token（勾选 `repo` 权限的 classic token）
3. 保存后到 **Actions** 页手动跑一次 `Daily Job Scan` 验证

## 运行测试

```bash
python -m pytest tests/ -v        # 离线单测（不依赖网络）
```

## 项目结构

```
crrc-job-radar/
├── run.py                 # CLI 入口：抓取 → 筛选 → 增量 → 报告
├── docs/jobs.md           # 每日自动更新的投递清单（GitHub Actions 生成）
├── crrc_radar/
│   ├── api.py             # 中车招聘云平台 API 封装（标准库 urllib，带重试）
│   ├── filters.py         # 关键词 + 城市筛选器
│   ├── scoring.py         # 岗位-简历匹配打分（技能档案比对，推荐 TopN）
│   ├── tracker.py         # 增量追踪：快照对比，新增岗位识别
│   └── report.py          # markdown 投递清单生成
├── .github/workflows/
│   ├── daily.yml          # 每日自动扫描（cron）
│   └── ci.yml             # 单元测试
└── tests/                 # 离线单元测试
```

## 说明

- 数据来源：中车招聘云平台公开接口（`crrc.hotjob.cn`），未登录即可访问
- 平台接口与字段可能调整，若失效请按 `crrc_radar/api.py` 注释更新
- 本工具仅做信息聚合与筛选，投递请以官网为准