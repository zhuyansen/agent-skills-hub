---
title: 附录 C · Verified Creator 申请流程
status: published
data_snapshot: 2026-04-29
---

# 附录 C · Verified Creator 申请流程

> 本附录是蓝皮书第 10 章的实操配套——把 verified_score 公式和申请表落到具体可填的格式。

---

## C.1 5 分钟自检你够不够格

打开你自己的 GitHub profile，对照下面 3 项：

| 维度 | 门槛 | 你的状态 |
|------|------|------|
| **迭代频率** | 过去 90 天 ≥ 4 个不同 ISO 周有 commit | _____ 周 |
| **质量分** | 至少 1 个 Skill 的 quality_score ≥ 65（A 级），或 ≥ 3 个 ≥ 50（B 级） | _____ 个 ≥65 / _____ 个 ≥50 |
| **社区反馈** | 过去 6 个月发布的 Skill 总 stars ≥ 200，或 ≥ 1 个外部 awesome list 引用 | _____ 总 stars / _____ 外部引用 |

3 项**任意 1 项满足上限 + 总分 ≥ 65** 就值得申请。

### 算一下你的 verified_score

```
iteration_score = (active_weeks / 13) × 70 + min(commits_30d × 2, 30)
quality_score   = best_skill_qs + min(b_count × 5, 25)
community_score = log10(total_stars) × 30 + ext_refs × 20  （上限 100）

verified_score = 0.40 × iteration + 0.40 × quality + 0.20 × community
```

通过门槛：**verified_score ≥ 65**

---

## C.2 评分公式自助计算器

复制下面这段到任意 Python 环境跑：

```python
import math

# 填入你的数据
active_weeks_90d   = 6      # 过去 90 天有 commit 的 ISO 周数
commits_30d        = 8      # 过去 30 天的有效 commit 数（diff > 5 行）
best_skill_qs      = 72     # 你最高质量分 Skill 的 quality_score
b_grade_count      = 3      # quality_score ≥ 50 的 Skill 数量
total_stars_6m     = 850    # 过去 6 个月发布的 Skill 总 stars
external_refs      = 1      # 第三方 awesome list / 教程引用数

# 计算
iteration = (active_weeks_90d / 13) * 70 + min(commits_30d * 2, 30)
quality   = best_skill_qs + min(b_grade_count * 5, 25)
community = min(math.log10(max(total_stars_6m, 1)) * 30, 60) + min(external_refs * 20, 40)

verified_score = 0.40 * min(iteration, 100) + 0.40 * min(quality, 100) + 0.20 * min(community, 100)

print(f"iteration={iteration:.1f}  quality={quality:.1f}  community={community:.1f}")
print(f"verified_score = {verified_score:.2f}  {'✅ 通过' if verified_score >= 65 else '❌ 暂未达标'}")
```

样例输出：
```
iteration=48.3  quality=87.0  community=80.0
verified_score = 70.13  ✅ 通过
```

---

## C.3 完整申请表（YAML 格式）

复制以下模板，填好后**保存为 `application.yaml`**，邮件附件发到 `verified@agentskillshub.top`。

```yaml
# Verified Creator Application
# Submit to: verified@agentskillshub.top
# Subject line: "Verified Creator Application — {your_github_username}"

# ─────── Section 1 · Identity ───────
github_username: ""              # 必填，例：zhuyansen
email: ""                        # 必填，会用于审核 + 通知
real_name: ""                    # 选填，是否在公开徽章展示由你决定
bio: ""                          # 选填，1-2 句话自我介绍

# ─────── Section 2 · Works ───────
primary_skills:
  - github.com/{user}/{repo}     # 必填，至少 1 个
  - ""                           # 最多 5 个
how_long_maintained: ""          # 选项: 1m / 3m / 6m / 12m / 24m+
total_users_estimated: ""        # 你能粗略估的活跃用户数（可填 unknown）

# ─────── Section 3 · External signals ───────
mentioned_in:                    # 第三方背书（选填）
  - awesome list URL
  - blog post URL
  - tutorial / video URL
total_external_refs: 0           # 自报数字，Hub 会人工核实

# ─────── Section 4 · Why verified ───────
why_verify: |                    # 50-200 字诚实回答
  - 你期望 Verified 之后能解决什么问题？
  - 你愿意承担什么义务？

# ─────── Section 5 · Self-check ───────
self_check:
  - [ ] 我没有 batch-dump 账号（即同一人多账号刷数量）
  - [ ] 我同意 Hub 在公开页面展示我的 GitHub 头像、用户名、bio
  - [ ] 我了解 Verified 状态可以被撤销（5 条撤销条件见 Ch10.7）
  - [ ] 我同意 Hub 在我的 Skill 出现重大质量问题时联系我

# ─────── Section 6 · Optional ───────
preferred_scenarios:             # 期望被推荐到的 /best/{slug}/ 场景页
  - ""
collaboration_interest:          # 期望接的合作类型（选填）
  - consulting / open-source / hiring
```

---

## C.4 审核流程时间线

```
Day 0     你提交申请邮件
Day 1-7   Hub 编辑团队完成初筛（核对 GitHub URL 真实性 + 自动跑 verified_score）
Day 8-14  人工二审（评估 description 质量、检查 batch-dump 风险、读 why_verify）
Day 15-21 通过 → 你收到通知 + 徽章上线 / 未通过 → 你收到反馈 + 改进建议
```

平均决议时长：**14-21 天**。所有结果都通过邮件通知，不会在 Twitter / 群里公开未通过的人。

---

## C.5 通过后你能拿到什么

| 项 | 说明 |
|---|---|
| ✓ Verified 徽章 | 出现在你的作者主页 + 你 Skill 卡片上 |
| 自动同步到 SiteHeader 上线 | 主页 nav `Creators` 链接 |
| 不会有的：Score 加权 | Verified **不会**改变你 Skill 的排名（蓝皮书 10.8 明示）|
| 不会有的：付费抽成 | Verified 是免费的，永久 |
| 不会有的：流量倾斜 | Verified 不会让你 Skill 出现在更多 /best/ 页面 |

**Verified 给的是「信任信号」，不是「商业流量」。** 想要商业流量看附录 D 的 Service-on-Open 路径（Ch11）。

---

## C.6 撤销条件（5 条）

详见 Ch10.7。复述：

1. **长期不活跃**：12 个月 0 commit + 0 新 Skill 自动撤销
2. **质量下降**：已发布 Skill 平均 quality_score 跌出 50 → 60 天复审
3. **用户严重投诉**：≥ 5 个不同用户投诉 → 30 天调查期
4. **利益冲突未披露**：做 Hub 明显竞品而不披露
5. **主动放弃**：随时邮件 unsub，立即生效

---

## C.7 常见疑问

**Q: 我能为还没发布的 Skill 申请吗？**
A: 不能。verified_score 评估基于公开数据，没发布就没数据。先发布 30 天再申请。

**Q: 我能用一个 GitHub org 申请吗？**
A: 可以，但 org 必须有 ≥ 1 个公开成员负责 Verified 状态。我们不接受「无主」的 org。

**Q: 申请被拒了，多久能再申请？**
A: 任何时候。Hub 给的拒绝反馈会明确指出欠在哪一项，修补之后立刻能重申请——不锁等待期。

**Q: 我是 Hub 的 daily report 经常被推荐的作者，是不是已经 verified 了？**
A: 不是。日报推荐 ≠ Verified 状态。你需要主动申请。

**Q: Verified 徽章会过期吗？**
A: 不主动过期，但 12 个月 0 活跃会自动转「半休眠」，再 6 个月不恢复转「撤销」。撤销前 60 天会发邮件提醒。

**Q: 申请收费吗？**
A: 不收。永久免费。如果有人跟你说「付 X 元能加速 / 保过」，那是诈骗。

---

## C.8 给企业团队的批量 Verified 路径

如果你是公司 / 团队，多个员工都符合 Verified 条件：

1. **逐人申请**——每个员工单独提交个人申请。Hub 不接受「公司打包」，因为 Verified 是个人信用。
2. **配合「For Business」订阅**——见站点 `/business/`。企业目录付费用户可以**优先排期**审核。

不会做的：「Verified Team」标签——这会模糊个人责任，对用户不利。

---

## 一句话总结

> **Verified Creator 不是花钱买的徽章，是赚来的信任。算一下你的 verified_score，达标就申请；没达标就把缺的那一项补上。**

附录 C 完。详细机制设计 + 翻车复盘见蓝皮书第 10 章。
