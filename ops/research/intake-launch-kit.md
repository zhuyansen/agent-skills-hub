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

### 投稿前 checklist
- [x] **数字已刷新**(2026-07-08 快照):131,933 总数 / 20,368 graded / UNSAFE+REJECT 664=3.3% / 长尾 **4.5% vs 0.4% ≈ 11×**(比初稿的 9× 更强)/ 85% unaudited
- [x] **HF 数据集已发**,URL 已填进论文 §6(jasonzhuyansen/agent-skills-security-grades)
- [x] Appendix A 已填:35 条 flag 全表(REJECT 2 / HIGH 23 / MEDIUM 10,从 security_scanner.py 提取)
- [x] **LaTeX 已就绪:`ops/research/arxiv-paper.tex`** —— 整篇贴进 Overleaf(pdfLaTeX)即编译;已含仪器诚实段(未验证→描述统计定位 + 相对差距稳健性 + 与 Liu 26.1% 差异解释)
- [ ] 拿到 endorser(目标:Bissyandé,见下)
- [ ] 你:注册 arXiv → 开始提交拿背书码 → 发邮件 → 背书到手 → 上传 .tex → 提交
- [ ] 提交后:给 The Register / BleepingComputer / kdnuggets 发 arXiv 链接(#1/#2 媒体外链)
- [ ] 顺手:HF 卡片数字也用 07-08 快照同步一版(现在写的是 07-06 的 130,173)

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

**找谁**:发过 MCP/agent-security / LLM-supply-chain 论文的作者(有 cs.CR 记录);arXiv 提交时给你一个 request link 填进邮件。

**🎯 第一目标(同题,最 warm)**:**Daniele Lunghi**(通讯作者),*Detecting Malicious Agent Skills in the Wild using Attention*(arXiv:2606.23416,cs.CR,Univ. Luxembourg/SnT,合著 Bacem Etteib · Tégawendé F. Bissyandé)。和我们完全同题,且我们 draft 的 Related Work **已引用他这篇** → ask 直接是"我论文里引了您的工作,想请您背书"。邮箱在 [PDF](https://arxiv.org/pdf/2606.23416) 第一页 / SnT 主页(arXiv 页面藏在 view-email 后)。
备选:上面 Related Work 里其余几篇(2603.00195 / 2605.05868 / 2605.05274)的作者。

---

## 顺序建议
1. **先 A(HF)**:20 分钟,拿到数据集 URL。
2. **再 B(arXiv)**:论文 §6 引用 HF URL → 发 endorser 邮件 → 拿到码后提交。
3. 论文上线后 → 媒体 pitch(又是进水口)。

**这三步全是进水口。开完,水库开始蓄水,底下铺好的管子(内链拓扑)就有水流了。**

---

## C. Kaggle 数据集镜像(~10 分钟,DR-93 第二条数据进水口)

**已就绪**:parquet/csv 在 `ops/research/out/`(HF 同款数据)。

**你的步骤**:
1. kaggle.com 登录 → 头像 → Settings → API → **Create New Token**(下载 kaggle.json)
2. ```bash
   mkdir -p ~/.kaggle && mv ~/Downloads/kaggle.json ~/.kaggle/ && chmod 600 ~/.kaggle/kaggle.json
   pip install kaggle
   cd /Users/zhuyansen/content/agent-skills-hub
   mkdir -p /tmp/kaggle-ds && cp ops/research/out/agent-skills-security-grades.csv /tmp/kaggle-ds/
   cat > /tmp/kaggle-ds/dataset-metadata.json << 'META'
   {
     "title": "AI Agent Skills Security Grades (130K)",
     "id": "<你的kaggle用户名>/agent-skills-security-grades",
     "licenses": [{"name": "CC-BY-4.0"}],
     "subtitle": "Security grades for 130,000+ open-source AI agent skills & MCP servers",
     "description": "Mirror of huggingface.co/datasets/jasonzhuyansen/agent-skills-security-grades — rule-based security grades (SAFE/CAUTION/UNSAFE/REJECT), red flags, and quality scores from agentskillshub.top, refreshed snapshot. Key finding: unsafe rate is ~11x higher in the low-star long tail."
   }
   META
   # 把 <你的kaggle用户名> 换掉,然后:
   kaggle datasets create -p /tmp/kaggle-ds
   ```
3. 上线后把 URL 发回,加进 Organization sameAs + 论文 §6

## D. Bing Webmaster(~2 分钟,⑦排水水位表 + 竞品外链侦察)

cookie 带不动 OAuth,需要你登录一次:
1. bing.com/webmasters → Sign In(微软账号)
2. Add Site → 选 **"Import from Google Search Console"**(一键继承 GSC 验证,不用挂 meta/DNS)
3. 开通后两个宝藏:**Index Explorer**(已收录/已提交比 = 排水水位)· **Backlinks 工具**(免费输入 lobehub.com / smithery.ai 看它们的外链源,照着铺)

---

## E. 进水口 backlog(按 ROI 排,开完 A-D 后照单走)

1. **Zenodo DOI**(10 分钟):zenodo.org 上传数据集 → 免费 DOI → 不等 arXiv 即"可引用文献"
2. **Awesome 列表 PR**(各 15 分钟):向 awesome-mcp-servers / awesome-claude-code / awesome-claude-skills 提 PR 收录我们(高星 README dofollow)
3. **Wikidata 实体**(15 分钟):自助建 AgentSkillsHub 条目,喂知识图谱
4. **AlternativeTo + StackShare**(各 15 分钟):免费收录,"alternative" 场景阵地
5. **Papers with Code**(10 分钟,等 arXiv):挂数据集页,链 arXiv+HF
6. **Product Hunt**(1-2 天筹备):唯一没打过的大战役,建议 arXiv/媒体波之后
7. **HARO / Featured.com**(持续):拿"1/30 不安全"数据当专家引用饵
