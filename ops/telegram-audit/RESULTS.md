# Telegram bot source audit, 2026-10-10

Read from each repo's source; nothing was run. Evidence (file and line) is in results.json.

## Bots that drive a coding agent on your machine (14)

| # | Bot | ★ | With no allowlist | Before the agent acts | Setting |
|---|---|---:|---|---|---|
| 1 | grinev/opencode-telegram-bot | 1234 | Serves nobody | Agent's own prompts sent to Telegram | TELEGRAM_ALLOWED_USER_ID (required) |
| 2 | alexei-led/ccgram | 277 | Serves nobody | Permission prompts sent to Telegram | ALLOWED_USERS (required) |
| 3 | six-ddc/ccbot | 276 | Serves nobody | Permission prompts sent to Telegram | ALLOWED_USERS (required) |
| 4 | banteg/takopi | 1049 | Serves nobody | Runs with permission prompts off | chat_id (required); allowed_user_ids for groups |
| 5 | duckbugio/flock | 502 | Serves nobody | Runs with permission prompts off | ALLOWED_USERS |
| 6 | PleasePrompto/ductor | 457 | Serves nobody | Runs with permission prompts off | allowed_user_ids (required) |
| 7 | linuz90/claude-telegram-bot | 448 | Serves nobody | Runs with permission prompts off | TELEGRAM_ALLOWED_USERS (required) |
| 8 | smixs/agent-second-brain | 391 | Serves nobody | Runs with permission prompts off | ALLOWED_USER_IDS |
| 9 | emreturkmencom/antigravity-telegram-suite | 172 | Serves nobody | Runs with permission prompts off | ALLOWED_CHAT_ID (required) |
| 10 | NachoSEO/claudegram | 153 | Serves nobody | Runs with permission prompts off | ALLOWED_USER_IDS (required) |
| 11 | earlyaidopters/claudeclaw | 173 | Side commands open to anyone | Runs with permission prompts off | ALLOWED_CHAT_ID |
| 12 | overwirehq/claude-code-telegram | 2802 | Serves anyone | No prompts; kept to one directory | ALLOWED_USERS, and ENVIRONMENT=production |
| 13 | godagoo/claude-telegram-relay | 326 | Serves anyone | Depends on your Claude Code settings | TELEGRAM_USER_ID |
| 14 | hanxiao/claudecode-telegram | 608 | Serves anyone, no setting to change it | Runs with permission prompts off | none exists |

## Chat-only bots (6)

| # | Bot | ★ | With no allowlist | Before the agent acts | Setting |
|---|---|---:|---|---|---|
| 1 | tbxark/ChatGPT-Telegram-Workers | 3808 | Serves nobody | chat only | allowedUserIds (deny by default) |
| 2 | altryne/chatGPT-telegram-bot | 1637 | Serves nobody | chat only | TELEGRAM_USER_ID (required) |
| 3 | father-bot/chatgpt_telegram_bot | 5537 | Serves anyone | chat only | allowed_telegram_usernames |
| 4 | yym68686/ChatGPT-Telegram-Bot | 1290 | Serves anyone | chat only | whitelist, ADMIN_LIST |
| 5 | V-know/ChatGPT-Telegram-Bot | 649 | Serves anyone, no setting to change it | chat only | none exists (rate limits only) |
| 6 | polakowo/gpt2bot | 442 | Serves anyone, no setting to change it | chat only | none exists |
