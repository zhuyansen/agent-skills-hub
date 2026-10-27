# WorkBuddy 开放平台连接器（2026-10-26 准备，10-27 换成 0.11.0 / 0.6.0）

两个包，都是「MCP + Skill」方案，key 用「用户自填 Token 模式」（只存用户本机）：

| 包 | 锁定版本 | 表单 | 必填 |
|---|---|---|---|
| `backlink-guard.zip`（外链检测） | backlink-guard 0.11.0 + mcp 2.3.0 | Glasser / AIsa / GoAnyAPI key | 都选填（免费工具不用 key） |
| `new-term-radar.zip`（新词雷达） | new-term-radar 0.6.0 + mcp 2.3.0 | AIsa key、GoAnyAPI key、数据目录 | AIsa key、数据目录 |

格式照 open.workbuddy.cn/docs/connector 和 /docs/skill：`connector-meta.json`、`mcp.json`（一个 stdio 服务器）、`token-schema.json`、`icon.svg`、`skills/<名字>/SKILL.md`（带 display_name、description_zh/en、version、author）。zip 里是一层文件夹再放文件，和文档里的目录树一致；平台若解析失败，改成文件直接放在 zip 根目录再试。

## 你要做的

1. 在 open.workbuddy.cn 入驻：个人认证要本人中国大陆二代身份证、实名手机号、邮箱和刷脸（海外主体、港澳台和外籍证件都不收）。也可以用国内公司做企业认证。
2. 设开发者昵称。两个 skill 的 `author` 写的是 "Jason Zhu"，昵称不一样的话告诉我改成一致。
3. 开发 → 连接器 → 上传 zip，一个包提交一次。
4. 平台要填的说明（开发者协议 §2.1.2：功能、运行条件、测试方式、依赖、收费、权限和数据用途）照下面两段填。
5. 审核要测付费工具的话可能得给一个测试 key：建议单开一个、只充少量额度，审完删掉。

## 提交说明：外链检测

- **功能**：提交外链前查来源是不是垃圾站，上线后查链接在不在、传不传权重，给自己的外链做垃圾外链体检；还能找该出现的页面、竞品有而你没有的外链、竞品上线头 90 天拿到的外链（和你同龄时比，列出你还没有的发布清单）、某个来源最近还收不收新站、Google AI 概览引用了谁、AI 助手怎么回答。工具从不替用户提交任何东西。
- **运行条件**：本机装 uv（https://docs.astral.sh/uv/）；WorkBuddy 4.24.0 及以上。第一次连接时 uvx 从 PyPI 下载 backlink-guard 0.11.0 和 mcp 2.3.0。
- **测试方式**：不填 key 就能测 `verify`、`submissions` 和 `vet`（`free=True`，加 `newcomers=True` 也免费）；其余工具要 Glasser 或 AIsa 的 key。
- **依赖**：PyPI 包 backlink-guard（MIT，源码 github.com/zhuyansen/backlink-guard）和 mcp。
- **收费**：连接器本身免费。付费数据由用户自己的 Glasser / AIsa / GoAnyAPI 账户按量计费，每次付费调用前 AI 先报价、等用户同意；价格见 README 的工具表。key 表单里的注册链接是作者的推荐链接，表单里写明了，从官网直接拿的 key 一样能用。
- **权限和数据用途**：key 只存在用户本机，连接时作为环境变量交给本机的服务器。工具会读取用户让它查的网页，把要查的域名和关键词发给 Glasser、AIsa、GoAnyAPI 的接口。提交记录和缓存存在本机 `~/.backlink-guard`。不收集个人数据。

## 提交说明：新词雷达

- **功能**：在 X、Hugging Face、GitHub 和网站地图里找刚出现的 AI 模型、产品和仓库名，用 Google Ads 搜索量和 DataForSEO Trends 给背后的搜索词估量、看走势，给出优先、观察或跳过。词表还给出近 12 个月的走势、词第一次被搜的时间和各国市场、首页的样子（AI 概览、论坛帖）、用户自己的排名和该更新还是新建页面、同名 .com 有没有被注册；新站信号带上新站最先排上的词。
- **运行条件**：本机装 uv；WorkBuddy 4.24.0 及以上；数据目录要填本机一个能写的绝对路径。第一次连接时下载 new-term-radar 0.6.0 和 mcp 2.3.0。
- **测试方式**：`recent_leads` 免费（数据目录里没跑过雷达时返回空）；`keyword_table` 和 `run_radar` 要 AIsa key。
- **依赖**：PyPI 包 new-term-radar（MIT，源码 github.com/zhuyansen/new-term-radar）和 mcp。
- **收费**：连接器本身免费。`keyword_table` 每个名字约 0.05 USD，每次调用另加 0.09 USD；`run_radar` 的 `daily` 在示例配置下约 0.30 USD。都从用户自己的 AIsa 账户扣，调用前 AI 先报价、等用户同意。推荐链接同上。
- **权限和数据用途**：key 只存本机。会请求 AIsa（X 帖子、搜索量、Trends、判断名字的模型）、GoAnyAPI、Hugging Face、GitHub 和配置里的网站地图。数据库存在用户填的数据目录里。
- **已知限制**：`keyword_table` 每个名字 40 到 90 秒，`daily` 5 到 15 分钟，超过平台建议的单次 30 秒；`mcp.json` 的 `timeout` 设了 300 秒。

## 本机验证过什么，没验证什么

- **验证过**：照 `mcp.json` 的命令从 `/` 启动、key 留空：外链检测的 `submissions`、`verify`、`vet(free=True)` 正常；雷达填了数据目录后 `recent_leads` 正常，不填数据目录就报只读文件系统的错（所以设成必填）。JSON 都能解析，`${…}` 占位符和表单字段一一对应。
- **没验证**：本机没装 WorkBuddy，表单显示、占位符替换和 `timeout` 的含义都没实测。选填的 key 留空时，WorkBuddy 如果不是填空字符串而是原样留着 `${GLASSER_API_KEY}`，会被当成一个错误的 key（Glasser 回 401）。
- **报错原因**：0.10.0 和 0.5.1 出错时 agent 只看到「Error executing tool …」（mcp 2.x 的行为），10-26 发的 0.10.1 和 0.5.2 起把原因带给 agent（没 key、key 被拒、数据目录写不进）。10-27 两个包换成 0.11.0 和 0.6.0（外链检测的 SKILL.md 补了 `early`、`newcomers` 两段）。以后发新版，照下面换版本号、重新打包再提交：

```bash
cd ops/workbuddy
sed -i '' 's/0\.11\.0/新版本/g' backlink-guard/connector-meta.json backlink-guard/mcp.json backlink-guard/skills/backlink-guard/SKILL.md
sed -i '' 's/0\.6\.0/新版本/g' new-term-radar/connector-meta.json new-term-radar/mcp.json new-term-radar/skills/new-term-radar/SKILL.md
rm -f *.zip && for n in backlink-guard new-term-radar; do zip -q -r -X $n.zip $n -x '*/.DS_Store'; done
```
