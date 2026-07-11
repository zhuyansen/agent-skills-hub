# Reddit 养号计划(30 天,2026-07-11 起)

> 目标:把新账号养成"有真实评论史 + 有 CQS 信任分"的可信号,为 arXiv 数据帖铺路。
> 依据:[[backlink-todo]] §Reddit 作战卡 v2(吸收 Alisa 230 万 views 复盘)。
> 铁律(前 3 周):❌ 不贴链接 ❌ 不提 agentskillshub ❌ 不复制粘贴同一条评论。刷的是信任分,不是曝光。
> 每天 ≤20 分钟,人时红线内。发帖等 arXiv ID + 账号满 2-3 周双条件。

## 一次性准备(Day 0,10 分钟)

- [ ] reddit.com 注册(常用邮箱,**别买号**;用户名中性、别带 agentskillshub)
- [ ] Join 两个主战场:[r/mcp](https://www.reddit.com/r/mcp/) · [r/ClaudeAI](https://www.reddit.com/r/ClaudeAI/)
- [ ] 补 Join 两个备选(评论用,不主攻):[r/LocalLLaMA](https://www.reddit.com/r/LocalLLaMA/) · [r/ChatGPTCoding](https://www.reddit.com/r/ChatGPTCoding/)
- [ ] 各读一遍 sidebar 规则(能不能发链接、要不要 flair、有没有 self-promo 限制)
- [ ] 头像+一句 bio(证明是真人;bio 别写营销词)

## 每日 20 分钟节奏(固定在刷 X 的同一时段)

| 时段 | 动作 | 要点 |
|---|---|---|
| 前 5 min | 开 [r/mcp/rising](https://www.reddit.com/r/mcp/rising/) + [r/ClaudeAI/rising](https://www.reddit.com/r/ClaudeAI/rising/) 浏览 | Rising = 正起量,评论能站前排;真觉得好就 upvote |
| 中 10 min | 挑 1-2 个真有话说的帖,写 **20 词+英文评论** | 见下"五种满分姿势";写不出宁可只点赞 |
| 后 5 min | 给别人优质评论点赞;看昨天自己的评论有没有人回,有就接着聊 | 对话延续 = CQS 最爱的信号 |

**五种满分评论姿势**(任选,都不带链接不带品牌):
1. 补案例:"我真遇到过 X,当时是这么处理的……"
2. 给方案:"更省事的办法是 Y,一行命令就能试"
3. 提坑:"注意 Z,楼主这个配置在……场景会炸"
4. 拆问题:"你其实在问两件事:一是……二是……"
5. 纯干货答技术问题(最稳)

**样板评论**(r/mcp 有人问"怎么判断一个 MCP server 靠不靠谱"):
> Two things I always check before adding one to my config: what scopes/env vars it actually reads (grep for process.env — a surprising number request way more than they need), and whether the last commit is newer than three months. Stars honestly tell you very little; maintenance tells you a lot.

## 三周里程碑(勾选看进度)

**Week 1(Day 1-7)· 潜水期**
- [ ] 每天到岗 20 min(允许 1 天断)
- [ ] 累计 ≥10 条真实评论
- [ ] Comment Karma 破 20
- [ ] 摸清两个社区各自的"语气"(r/mcp 偏技术、r/ClaudeAI 偏用户体验)

**Week 2(Day 8-14)· 建立存在感**
- [ ] 累计 ≥25 条评论
- [ ] 至少 3 条评论拿到 ≥5 upvote 或引出回复
- [ ] Comment Karma 破 50
- [ ] 试发 1 条**纯干货帖**(不带链接不带品牌,如"3 things I learned debugging MCP servers this week")—— 练手 + 攒发帖信任

**Week 3(Day 15-21)· 具备发帖资格**
- [ ] 累计 ≥40 条评论
- [ ] Comment Karma 破 100
- [ ] 账号龄 ≥21 天(很多 subreddit 的 Automod 门槛)
- [ ] 观察:在 r/mcp 发帖被秒删过没?(没有=信任够了)

## 发帖点火条件(两个都满足才发)

1. ✅ **arXiv ID 到手**(数据帖的镇楼弹药)
2. ✅ **账号满 3 周 + Karma 100+**

**首帖**(数据故事体,文章实测最易起量):
- 标题:`I security-graded 130,000 MCP servers — 83% have never been audited. Patterns inside.`
- 正文:TL;DR + 表格(对人对 LLM 都友好)→ 3-4 个具体发现 → 方法论诚实声明(规则扫描非逐行审计)
- **链接放评论区第一条**(帖里放太多链接被降权),arXiv + 数据集
- 发后**前 2 小时守评论**:补信息、认不足、接质疑
- 平台错峰:周二上午美东发 r/mcp,隔天改写角度发 r/ClaudeAI(别复制粘贴)

## 长期(发完首帖后)

- **评论寄生**:用具体长尾词(不是泛词)找 7 天内新帖介入;**回自己老帖补 UPDATE 成功率最高**(月报每月给一次保鲜理由)
- **官网反哺**:写 `/blog/safe-mcp-servers-reddit/` 承接页(LLM 检索会带 "reddit" 关键词)
- **绝不**:一天多帖、跨社区复制粘贴、karma 农场、买赞(实测几小时掉光 + 触发风控)

---
*进度每周一复盘时对一次;养号是慢功夫,断 1-2 天没关系,别断成"想起来才做"。*
