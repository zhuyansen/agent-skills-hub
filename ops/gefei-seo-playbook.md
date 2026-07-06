# 哥飞会议 SEO 干货提炼 → AgentSkillsHub 应用

> 来源:gefei-meetings.vercel.app 三条线下会议记录(2026-07-04)。
> 每条 = 哥飞方法论 + 我们的具体落地动作。多条印证了我们已在做的判断。

## 1. AI 时代 SEO 变天(印证我们的 GSC 发现)
**哥飞**:AI Overview + 广告 + YouTube + PAA 挤压自然结果,"排名第一点击率也极低"。
→ 我们 GSC 实测 pos 6-9 却 0.1-0.4% CTR = 同一现实,不是 bug。
**解药(=我们该做的)**:
- **寄生虫 SEO**:把安全报告/数据集发去 Reddit/HN/LinkedIn/Medium 高权重站,借权重(接 arXiv/HF 弹药)。
- **底部漏斗竞品拦截页**:"LobeHub alternative"、"is X safe"(/audit/ 已是雏形,扩)。
- 场景长尾:/best/{scenario} 继续挖具体词。

## 2. 品牌词:哥飞一句话定案
**哥飞**:"谷歌算法更新永远利好品牌,域名选好记的品牌名,别用 bestaixxx.com。"
→ 印证"Agent Skills Hub 类目词吃亏",但"更新利好品牌"=把品牌权威做起来 Google 越站你 → **权重线(arXiv/PR/数据)是对的,坚持**。

## 3. 新词挖掘:我们有现成雷达
**哥飞**:Google Trends 非源头;新词先在游戏主播/模型公司推特/AI 玩法博主(宝玉归藏)火;倒推源头+订阅 RSS+Twitter API 定时抓(半年内/高赞/带链接)。
→ 我们 sync 每 8h 扫全网 skill = 本赛道新词雷达;/skill/+/audit/ 天生第一时间落地。
**补的动作**:每周跑 `fetch_gsc.py brand` + compare,盯 rising queries,新工具名一被搜就确保排第一。

## 4. 外链:两免费招+一避坑(印证 16 行框架)
**哥飞**:
- **Bing 站长 backlinks 工具** = 免费看竞品外链,只显示必应已收录(自带质量过滤)。
- nofollow 来自高权重(HN)照样传权重,别嫌弃。
- Guest Post 买 $100+;DR 虚高低流量模板站不买。
→ 印证外链 16 行(#7/#15 别碰垃圾高 DR)。**新动作**:用 Bing backlinks 扒 LobeHub/smithery 外链发布地照着铺。

## 5. 转化:把用户当傻子(接 Clarity 数据)
**哥飞**:价格页跳出最高→离开前弹打折;注册入口放最高流量页+复制/下载按钮;前端别用模板不改(信任→转化);手把手(预设提示词/示例图)。
→ 我们 Clarity 死点击 14.2% = 找不到入口。落地:/enterprise/ 和 $49 页加 exit-intent 弹窗;首页统计卡已改可点(死点击修复)。

## 6. 心态/执行(创业底层)
- 跑通**全链路**才赚钱,单点优秀只打工。
- 新手做**小词/新词**(正反馈快、门槛低),不抢大词。→ 我们 pSEO(117K skill 页+7924 audit 页)就是"堆量+小词"。
- SEO 是**放大器不是启动器**("攀珠峰到 6000m,不从零到顶")→ 先验证商业模式+做品牌,别一开始 all-in SEO。→ 我们已有 $49 收银台在验证商业模式,顺序对。

## 7. 后 5 条会议新捞干货
- ⚠️ **`.top` 域名被点名"不受搜索引擎信任、难收录"**(记录③)。我们就是 .top。叠加"类目描述名" = 品牌权重上不去的两刀。**短期不迁**(11万页+外链+GSC历史重来风险高),靠 arXiv/HF/PR 堆品牌权威;品牌真起来后再考虑 .com/.ai。
- **全页面用"高搜索量表述"选词**:"Midjourney prompts">>"Midjourney inspiration";登录/定价页都能优化。→ 用 GSC 数据校准 /category//best/ 标题精确措辞(MCP server vs servers、Claude skills vs Claude Code skills)。
- **截流三类词:需求词/竞品品牌词/模型词**,模型词转化最高(已有使用意图)。→ 建模型名落地页(Claude Code skills / Cursor MCP / GPT-5 agent tools)+ 竞品 alternative 页。
- **找大佬抄盘**:大词短时上首页/新词最快冲上去=大佬;抄其外链+新关键词;`intitle:` 看结果增速判断词会不会爆。→ 盯 LobeHub/smithery/glama。
- **定价页 3 档锚定中间 + 默认年费**(年费总价<月费年化)。→ $49/enterprise 定价页照此。
- **冷门细分 > 热门模型词**(排名易度):模型词截流拿意图,长尾拿排名,两条腿 = 印证我们 /best//audit/ 策略。
- 小语种:子目录竞争小反哺整站权重,但**关键词不能直译要查本地真实搜索词**。中文 SEO 若认真推再用,优先级低。

## 立即可做(新增,非重复)
1. 每周 `fetch_gsc.py brand` + compare,盯 rising queries(新词雷达)。
2. Bing 站长 backlinks 扒竞品外链发布地 + 抄大佬新上关键词。
3. 寄生虫 SEO:安全报告/数据集发 Reddit/HN/Medium(接 arXiv/HF)。
4. 模型名截流页(Claude Code skills / Cursor MCP…)+ "LobeHub alternative" 竞品页。
5. 用 GSC 数据校准 category/best 标题的精确措辞(高搜索量表述)。
6. $49 + /enterprise/ 定价页:3 档锚中间 + 默认年费 + exit-intent 弹窗。
