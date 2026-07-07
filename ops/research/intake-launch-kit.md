# 进水口弹药清单 — arXiv + HF 上传

> 两个最硬、最天然被引用的进水口。AI 能做的全备好了,**只差你按发送键**。
> 对应 [[seo-watersystem-model]] 的 ① 进水口。一个下午能开两个。

---

## A. HuggingFace 数据集(~20 分钟,基本就绪)

**已就绪(AI 做完)**:
- ✅ 数据导出:`ops/research/out/agent-skills-security-grades.parquet`(5.9M)+ `.csv`(15M),130,173 行
- ✅ 数据卡:`ops/research/hf-dataset-card.md`
- ✅ `hf` CLI 已装(`/opt/homebrew/bin/hf`)

**你要做(4 步命令)**:
```bash
# 1. 登录(去 huggingface.co/settings/tokens 建一个 WRITE 权限 token,粘进来)
hf auth login

# 2. 命名空间:用你的 HF 用户名,或先建组织 huggingface.co/organizations/new
#    下面把 <NS> 换成你的用户名或组织名(例:agentskillshub)
export NS=<你的HF用户名或组织>

# 3. 建数据集仓库(hf upload 也会自动建,这步显式建更清楚)
hf repos create $NS/agent-skills-security-grades --repo-type dataset

# 4. 上传数据 + 卡片(卡片当 README.md)
cd /Users/zhuyansen/content/agent-skills-hub
hf upload $NS/agent-skills-security-grades ops/research/out/agent-skills-security-grades.parquet --repo-type dataset
hf upload $NS/agent-skills-security-grades ops/research/out/agent-skills-security-grades.csv --repo-type dataset
hf upload $NS/agent-skills-security-grades ops/research/hf-dataset-card.md README.md --repo-type dataset
```

**上传前微调卡片**(可选,让 HF 页面干净):删 `hf-dataset-card.md` 顶部两行 `# HuggingFace dataset card…` / `# Create at…` 注释,以及底部 `## Export script` 那段(都是给自己看的备注)。YAML frontmatter 本身合法,不删也能传。

**上传后**:数据集页 URL = `huggingface.co/datasets/$NS/agent-skills-security-grades`。这条链接就是进水口 —— 回填进 arXiv 论文、博客、GitHub README 的 sameAs。

---

## B. arXiv 论文(需 endorser + 你提交)

**已就绪(AI 做完)**:
- ✅ 全文草稿:`ops/research/arxiv-paper-draft.md`(7 页,cs.CR 主 / cs.SE 交叉)
- ✅ 大纲:`ops/research/arxiv-outline.md`

**卡点**:arXiv **首次投 cs.CR 需要一个 endorser**(已在 cs.CR 发过文、有背书资格的人)。

### 投稿前 checklist(提交当天)
- [ ] **刷新所有数字**:提交当天从 Supabase 重跑(总数/graded/各 grade/长尾分桶)—— 草稿是 07-06 快照,数字每天变
- [ ] **先发 HF 数据集**(A 部分),把 URL 填进论文 §6 Availability
- [ ] 填 Appendix A:从 `backend/app/services/security_scanner.py` 抄全 43 条 red-flag
- [ ] 排版:Overleaf + arXiv article class,~7 页
- [ ] 拿到 endorser(见下)
- [ ] 提交后:给 The Register / BleepingComputer / kdnuggets 发 arXiv 链接(#1/#2 媒体外链)

### Endorser 邀请邮件草稿(你填收件人 + 发送)

> **Subject:** arXiv endorsement request — cs.CR survey of 130K AI agent skills
>
> Hi Dr. {LastName},
>
> I'm an independent researcher preparing to submit a short empirical paper to
> arXiv cs.CR and, as a first-time cs.CR submitter, I need an endorsement.
>
> The paper — *The Long Tail Is Unaudited: A Security Survey of 130,000
> Open-Source AI Agent Skills and MCP Servers* — collects and rule-based
> security-grades 130,173 agent skills / MCP servers from GitHub. The central
> finding is distributional: the UNSAFE rate is ~9× higher in the low-star
> long tail (3.8% at 5–20 stars) than among popular repos (0.4% at 1000+),
> while 83% of the ecosystem is unaudited — exactly where marketplaces give
> users no signal. I'm releasing the full graded dataset (HuggingFace) and the
> scanner rules.
>
> Draft (7 pp) + dataset here: {LINK_TO_DRAFT_OR_HF}
>
> Endorsing only confirms the work is appropriate for cs.CR — it's not
> authorship or a review. If you're willing, arXiv will email you a code; my
> arXiv endorsement request link is: {ARXIV_ENDORSE_LINK}
>
> Happy to answer anything. Thank you for considering it.
>
> Best,
> Jason Zhu · agentskillshub.top

**找谁**:发过 MCP/agent-security / LLM-supply-chain / npm-typosquatting 论文的作者;或你认识的任何有 cs.CR 记录的人。arXiv 也有 endorsement 页会给你一个 request link 填进邮件。

---

## 顺序建议
1. **先 A(HF)**:20 分钟,拿到数据集 URL。
2. **再 B(arXiv)**:论文 §6 引用 HF URL → 发 endorser 邮件 → 拿到码后提交。
3. 论文上线后 → 媒体 pitch(又是进水口)。

**这三步全是进水口。开完,水库开始蓄水,底下铺好的管子(内链拓扑)就有水流了。**
