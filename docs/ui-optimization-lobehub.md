# UI 优化方案(对照 LobeHub /skills)

> 原则:**抄 LobeHub 的信息架构 + 打磨,但把我们独有的 Trust 信号(质量分 + 安全等级)做成视觉主角** —— LobeHub 这两样都没有。不做无脑复制。
> 现状对照:我们 SkillCard 已有 `quality_score / security_grade / stars / forks / category / platforms / author / last_commit`(信任信号比它丰富);缺 `安装量 / 评分 / 收藏 / curated 合集页 / 持久分类侧栏 / agent-first 安装框`。

---

## ① 导航栏(SiteHeader)

| LobeHub | 我们现状 | 可执行改动 |
|---|---|---|
| 顶栏极简:Products / **Community(超级菜单)** / Resources / Pricing + **GitHub 78.6K** + Get started | 图标一堆(GitHub/X/RSS/微信/主题/语言/Newsletter),略乱 | 1. 加一个 **「浏览」超级菜单**:鼠标悬停展开,显示我们的分类(MCP Server / Claude Skill / Agent Tool / Codex…)**带实时数量**(用 `get_landing_data` 的 category counts)+ 热门场景。这是 LobeHub Community 菜单的等价物。<br>2. 顶栏放 **GitHub star 数徽章**(像它的 78.6K),链到我们 repo。<br>3. 把 X/RSS/微信收进一个「···」或 footer,顶栏只留:浏览▾ / 企业 / 博客 / GitHub★ / 语言 / Get started。 |

**优先级:中**(改动小、立竿见影提质感)。

---

## ② 卡片设计(SkillCard)—— 最关键,把 Trust 做成主角

LobeHub 卡片:头像 + 名 + Featured 徽章 + ★评分 + 作者 + GitHub + 描述 + 文档数 + 分类徽章 + 日期 + ⬇下载量 + ★stars + 💬评论 + 🔖收藏。

**我们的改法(差异化,不照抄):**

1. **安全等级做成醒目彩色徽章** 🟢 SAFE / 🟡 CAUTION / 🔴 UNSAFE / ⚪ UNAUDITED —— 放卡片右上角,**这是 LobeHub 整站没有的信号**,要最显眼。
2. **质量分做成可视化**(环形 or 0-100 数字徽章),不要只是小字。
3. **采用度代理信号**:我们没安装量,但有 `star_momentum`(star 增速)→ 显示 **「↑ 本周 +X★」** 或 Trending 火苗,补上 LobeHub 的「安装量」社交证明位。
4. **加收藏 🔖**:localStorage 存(单设备 UI 偏好,符合我们架构红线),不需要后端。
5. 元数据行对齐 LobeHub 的密度:`category badge · platforms · ★stars · ↑增速 · 更新日期`。
6. 卡片整体收紧到它那种干净 3 列网格 + hover 微抬。

**优先级:高**(卡片是全站复用最多的组件,改一处全站受益;且直接把我们的护城河可视化)。

---

## ③ 认证用户/组织子页面(借 LobeHub「Curated Collection」)

LobeHub 的认证页 = `/skills/{collection}`:头像 + **「Top N {Name} Skills」** + 副标 + **「一键安装全部(Install all with one prompt)」框**(agent-first 可复制命令)+ 该作者 skill 卡片网格。

**我们已有 `/author/:username`(AuthorPage)和 Verified Creator/Org 概念 —— 直接升级成这种合集页:**

1. **AuthorPage 改版成合集页**:顶部大头像 + **「{作者} 的 Top Skills」** + 该作者全部 skill 卡片网格(复用新 SkillCard)。
2. **认证作者/机构加 ✓ 徽章** + 专属底色(我们有 `isVerifiedOrgAuthor()` / VERIFIED_CREATORS 数据)。
3. **「一键喂给你的 agent」框**(agent-first,接我们的 ash CLI):
   ```
   把这条贴给你的 agent,一次装齐 {作者} 的精选 skill:
   npx @agentskillshub/cli install {repo1} {repo2} ...
   ```
   —— 这正好把调研结论里「agent-first 安装」落地,且每条命令带我们的 Trust 预检。
4. **Verified Organizations**(高德等)用同一套合集页模板,机构 logo + 认证 ✓ + 精选 skill。

**优先级:高**(认证页是 Verified Creator 变现的展示位 + 拿外链的载体,且复用现有 AuthorPage/数据,工作量可控)。

---

## ④ 首页信息架构(借 LobeHub 的「侧栏 + 合集 + 多货架」)

LobeHub:左侧**持久分类侧栏(带数量)** + 顶部 **Curated Collection 行** + 多个横向货架(Most Installed / Trending / Highlighted / Recently Updated / Browse by Category)+ hero 里 **agent-first 安装提示框**。

我们现状:长竖滚、板块多但散(Hero→Ecosystem→ScenarioTagCloud→Problem→HowItWorks→InstallCli→Trending→NewThisWeek→TopRated→HallOfFame→Masters→…)。

**可执行改动:**
1. **Curated Collections 行**(首屏靠上):我们能策展的合集 —— 「MCP 安全精选」「Claude Code 必备」「网页抓取 Top」「Verified 机构」—— 复用 scenario/category 数据,做成 LobeHub 那种命名 pill 卡。
2. **Explore 视图加持久左侧分类侧栏 + 数量**(我们有 CategoryFilter,改成常驻 + 计数,像 LobeHub 左栏)。
3. **Hero 加 agent-first 安装框**:接 ash CLI(「把这条喂给你的 agent 发现+安全安装 skill」+ 可复制命令),呼应 InstallCliSection 但提到首屏。
4. 货架重排,**让我们的强项打头**:先 Trending(带安全徽章)+ Top Rated(质量分)+ New This Week,把 Trust 信号在首屏就铺满。

**优先级:中-高**(IA 改动较大,但 Curated 行 + agent 框可先做)。

---

## 推荐落地顺序(按 ROI)

1. **② SkillCard 改版**(安全彩色徽章 + 质量分可视化 + star 增速 + 收藏)← 全站复用、最高杠杆、把护城河可视化
2. **③ AuthorPage → 合集页**(认证 ✓ + 一键喂 agent 框)← 变现展示位 + 外链载体
3. **① 导航「浏览」超级菜单**(带分类数量)+ GitHub star 徽章
4. **④ 首页 Curated Collections 行 + hero agent 框**

**贯穿原则**:LobeHub 的牌是「多 + 美 + 一键」,我们的牌是「可信」。UI 每一处都要让 **security_grade / quality_score** 比它的安装量更扎眼 —— 否则就是用我们的短板(数量)去拼它的长板。
