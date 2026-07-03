# 深度审计交付 SOP(Concierge v1)

> 目的:/enterprise/ 和 analyzer 卖的"5 维深度审计"目前**人工交付**。这份 SOP 保证接到第一单时,任何人照着做 2-3 小时能交出专业报告。先手工卖掉 3 单,再谈自动化。

## 商品定义

| 项 | 内容 |
|---|---|
| 名称 | Deep Security Audit(单仓库) |
| 价格 | **$49 / repo**(首发价;企业批量另谈 → enterprise) |
| 交付物 | 一份 PDF/Markdown 报告(模板见下)+ 一条可引用的评级结论 |
| 时效 | **48 小时内**交付 |
| 范围 | 任意公开 GitHub 仓库(私有库需授权只读访问,+$30) |
| 收款 | v1 = 交付后 PayPal/支付宝/Stripe invoice(邮件里给链接);跑通 3 单后接 Stripe Payment Link |

## 接单流程

1. 收到邮件(subject 含 "Deep audit request")→ **24h 内回复确认**:repo、价格、交期、收款方式
2. 客户确认 → 开工;记录到 `ops/audit-orders.md`(日期/repo/客户/状态)
3. 交付报告 → 发 invoice → 收款 → 归档

## 审计执行(5 维,每维 30-40 分钟)

### 0. 基础数据(5 分钟,工具自动)
```bash
npx @agentskillshub/cli audit owner/repo --json   # 库内基础评级 + 红旗
# 打开 https://agentskillshub.top/analyzer?repo=https://github.com/owner/repo 截图实时扫描结果
```

### 1. Code(代码风险)
- [ ] clone 后通读入口文件 + 安装脚本(setup.sh / postinstall / SKILL.md 指令)
- [ ] 搜危险模式:`curl|bash`、`eval`、`exec`、base64 解码执行、混淆代码、外联下载
- [ ] 检查网络调用清单:所有外发请求的目的地列表(grep fetch/requests/httpx/axios)
- [ ] 沙箱跑一次(容器/一次性 VM),记录实际行为 vs 声称行为
- 结论分级:low / medium / high + 一句话证据

### 2. Credentials(凭证处理)
- [ ] 它要什么凭证(API key / OAuth / cookie / 文件系统权限)
- [ ] 凭证存哪(env / 明文文件 / 第三方托管 / 内存)
- [ ] 是否外传:凭证有没有可能到达作者或第三方服务器(重点!)
- [ ] 最小权限检查:要的权限和功能是否匹配

### 3. Vendor(维护者可信度)
- [ ] 作者真实身份可追溯?(GitHub 历史、公司、社交、其他项目)
- [ ] 账号年龄、活跃度、follower;是否匿名新号
- [ ] 有无公司主体 / 联系渠道 / 响应 issue 的记录

### 4. Supply-chain(供应链)
- [ ] 依赖清单审查:每个直接依赖的健康度(维护状态、是否 typosquat)
- [ ] lockfile 是否存在、依赖是否 pin 版本
- [ ] 上游有没有已知 CVE(`npm audit` / `pip-audit` / `cargo audit`)
- [ ] 构建产物 vs 源码一致性(npm 包内容 == repo 内容?)

### 5. Operational(运营风险)
- [ ] 服务依赖:它依赖的第三方 SaaS 挂了/被黑,影响面是什么
- [ ] 数据去向:处理的数据会不会离开本机
- [ ] 有无审计日志能力、能否回滚
- [ ] license 合规(商用限制?)

## 报告模板

```markdown
# Deep Security Audit — {owner/repo}
Agent Skills Hub · {date} · auditor: {name}

## Verdict
**{SAFE-FOR-PERSONAL | SAFE-FOR-PRODUCTION | CAUTION | REJECT}**
一句话结论(给决策者看的)。

## Dimension Summary
| Dimension | Risk | Key finding |
|---|---|---|
| Code | low/med/high | … |
| Credentials | … | … |
| Vendor | … | … |
| Supply-chain | … | … |
| Operational | … | … |

## Findings(每条:证据 → 影响 → 建议)
### F1 [severity] 标题
- 证据:file:line / 截图 / 命令输出
- 影响:谁会怎么受损
- 建议:怎么缓解

## Scope & Method
扫描工具版本、人工检查清单、沙箱环境、时间。
诚实声明:这是 point-in-time 审计,不构成对未来版本的担保。
```

## 红线

- **报告里每条 finding 必须有可复现证据**(file:line / 命令输出),没证据的不写
- 不夸大:没查到问题就写"未发现",别写"绝对安全"
- 客户 repo 的代码**不进公开渠道**(不发推、不进博客案例,除非书面同意)
- 交付前用模板自查:5 维全覆盖?verdict 一句话能站住?

## 自动化路线(卖掉 3 单后再动)
1. 维度 0/1/4 的命令行部分做成脚本(半自动)
2. LLM 辅助代码通读(audit-layers-todo Item 1)
3. SkillSpector 集成(Item 2)
