# MCP 注册站提交 · 状态与即贴内容(2026-07-03)

## 记分板

| 站 | 状态 | 链接 |
|---|---|---|
| npm | ✅ 已发布 | https://www.npmjs.com/package/@agentskillshub/mcp |
| **Glama** | ✅ **自动收录**(发布半小时内爬到,含 3 个 tool 子页) | https://glama.ai/mcp/servers/zhuyansen/agentskillshub-mcp |
| **mcp.so** | ✅ 已提交(GitHub issue) | https://github.com/chatmcp/mcpso/issues/2992 |
| **awesome-mcp-servers** | ✅ PR 已开(🤖🤖🤖) | https://github.com/punkpeye/awesome-mcp-servers/pull/9142 |
| **mcpservers.org** | 📋 网页表单,要邮箱 → 下面即贴 | https://mcpservers.org/submit |
| **PulseMCP** | ⏳ 自动爬虫(大概率几天内自己收录);想加速用表单 → 下面即贴 | https://www.pulsemcp.com/submit |
| **Smithery** | 📋 要登录他们账号 → 下面命令 | https://smithery.ai |

## mcpservers.org 表单即贴

- **Server Name**: `AgentSkillsHub`
- **Short Description**: `Search, audit, and install from 117K+ open-source AI agent skills & MCP servers — every result carries a security grade (SAFE/CAUTION/UNSAFE/UNAUDITED) and quality score checked BEFORE installing. Local cached index, works offline, no auth. Install: npx -y @agentskillshub/mcp`
- **Link**: `https://github.com/zhuyansen/agentskillshub-mcp`
- **Category**: `Search`(没有 Security 就选 Search 或 Development)
- **Contact Email**: 你的邮箱
- 💰 $39 premium(dofollow + 加速)可以不买 —— 免费队列就行

## PulseMCP 表单即贴(可等自动爬)

- **Name**: `AgentSkillsHub`
- **URL**: `https://github.com/zhuyansen/agentskillshub-mcp`
- **Description**: 同上 Short Description

## Smithery(要你的账号)

```bash
# 1. 登录(浏览器 OAuth)
npx @smithery/cli login
# 2. 发布(指向 npm 包)
npx @smithery/cli mcp publish @agentskillshub/mcp
```
如果 CLI 流程变了,直接在 smithery.ai 网页 "Add Server" 填 GitHub repo 地址即可。

## 收录后回访清单(一周后)

- [ ] Glama:认领(claim)server 页,补 logo/描述
- [ ] mcp.so issue 是否被处理;两周没动静去 issue 里礼貌 ping
- [ ] awesome PR 是否合并
- [ ] PulseMCP 是否自动出现(搜 agentskillshub);没有就提表单
- [ ] Cline MCP Marketplace(github.com/cline/mcp-marketplace 开 issue)—— 第二波
- [ ] 官方 registry.modelcontextprotocol.io —— 第二波
