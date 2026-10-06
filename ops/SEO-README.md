# SEO 文档索引

`ops/` 里讲 SEO 的文档有十几份,同一条规则常在几份里各写一遍。这页说清每份是干什么的、冲突时以哪份为准。2026-10-06 整理。

## 冲突时以谁为准

1. **页面怎么做**(标题、核心词、浪潮词、网址变更、FAQ、冲排名):`seo-watersystem-model.md` 的「页面级规则(2026-10 修订)」。
2. **整站怎么排优先级**(进水口、水库、内链、排水):`seo-watersystem-model.md` 的十个构件和施工顺序。
3. **具体怎么操作、用什么工具、踩过什么坑**:`seo-execution-guide.md`。
4. 哥飞会议笔记、大师库对照是**来源**,不是结论。它们和上面三份冲突时,以上面为准(修订时把原因写进去)。

日期更晚的结论优先。旧文档里被推翻的说法用删除线标出,不直接删,留着看当时为什么那样判断。

## 文档清单

| 文档 | 是什么 | 什么时候看 | 最后更新 |
|---|---|---|---|
| [seo-watersystem-model.md](seo-watersystem-model.md) | 通用模型:十个构件、施工顺序、铁律、判断清单、**页面级规则** | 做任何决策前 | 2026-10-06 |
| [seo-execution-guide.md](seo-execution-guide.md) | 执行手册:实践顺序、ROI 排序、工具安装与用法、27 条避坑 | 动手时 | 2026-10-06 |
| [seo-scoreboard.md](seo-scoreboard.md) | 记分板:周表(GSC 三列每周四自动填)、月表(人工) | 每周复盘 | 每周四自动 |
| [ppt-playbook.md](ppt-playbook.md) | PPT 页打法 + 复刻到新主题的清单 | 升级或新建一个主题页时 | 2026-10-06 |
| [ppt-retro.md](ppt-retro.md) | PPT 页 5 月到 10 月的每周数据和分阶段复盘 | 想知道某条规则从哪来 | 2026-10-05 |
| [gefei-seo-playbook.md](gefei-seo-playbook.md) | 哥飞会议、群聊、工具箱的方法论摘录 + 我们怎么落地 | 查哥飞原始说法 | 2026-10-06 |
| [seo-geo-timeline.md](seo-geo-timeline.md) | 3 月到 7 月的 SEO/GEO 动作编年史 | 复盘、给新站抄作业 | 2026-07-23 |
| [backlink-todo.md](backlink-todo.md) | 外链行动板和台账(权重层 / 发现层) | 做外链时 | 2026-07-26 |
| [research/masters-review-2026-07.md](research/masters-review-2026-07.md) | 十个出海大师库对照总汇(水系 v2 的修订依据) | 查信源 | 2026-07-23 |
| [research/niko-meeting-2026-07-23.md](research/niko-meeting-2026-07-23.md) | 外链两层论的会议记录 | 外链定位有疑问时 | 2026-07-23 |
| [research/channel-decision-tree.md](research/channel-decision-tree.md) | 什么产品该走什么渠道 | 上新产品前 | 2026-07-23 |
| [research/new-site-launch-checklist.md](research/new-site-launch-checklist.md) | 新站冷启动清单 | 建新站 | 2026-07-26 |
| [research/intake-launch-kit.md](research/intake-launch-kit.md) | arXiv、Hugging Face 等进水口的弹药 | 发数据集 / 论文时 | — |
| [launch-playbook.md](launch-playbook.md) | 安全报告的发布打法 | 发报告类内容时 | — |

## 已停用的数据源

- **Plausible**:试用 ~2026-08-03 到期,站点被锁,决定不续。建页前查重改用 GA 落地页(`fetch_ga.py`,已剔除机房无头浏览器)+ GSC 按页 + `grep` 现有 slug。旧文档里提到它的地方是历史记录。

## 改文档的约定

- 新结论先写进 `seo-watersystem-model.md` 或 `seo-execution-guide.md`,再在来源文档里留一句指向。
- 记分板历史行不改;数字错了在备注里勘误。
- 改完更新本页的"最后更新"列。
