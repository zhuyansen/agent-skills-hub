# YouTube 元数据:240+ 个 AI 做视频 Skill 排前十

视频:https://www.youtube.com/watch?v=1mm5863DyRc(2026-10-06 发布,2 分 07 秒,中文)
落地页:https://agentskillshub.top/best/claude-video-skills/(页面上已嵌入这条视频)
制作目录:`~/ship2market/sitedata/viral-clone/video-skills-A3/`

发布时的问题:

- **标题后面挂了 8 个 `##` 标签**(`##AI工具 ##AI做视频 …`)。标题里的 `#` 不会变成标签,`##` 更是原样显示,还挤掉了标题的有效长度。标签放进描述:描述里的前 3 个 `#标签` 会显示在标题上方。
- **描述里没有链接**,只写了"搜得到"。没有链接,看视频的人到不了页面,页面和视频之间也没有互相指向。
- 没有字幕、没有英文标题,分类是 People & Blogs。

## 1. 中文标题

```
240+ 个 AI 做视频的 Skill,只挑前十(只收安全评级 SAFE)
```

## 2. 中文描述(在原描述基础上加链接和章节)

```
让 AI 做视频的开源 skill 已经有 240 多个了,挑起来眼花😵

这期只收安全评级 SAFE 的,按 GitHub 星数排了个前十👇

完整榜单(240 多个,逐个读过 README、做了安全评级,可按类型筛选):
https://agentskillshub.top/best/claude-video-skills/?utm_source=youtube&utm_medium=video&utm_campaign=video-top10

GitHub 开源合集(每天自动更新):
https://github.com/zhuyansen/awesome-claude-video-skills

🥇 OpenMontage ★64.3k https://github.com/calesthio/OpenMontage
🥈 hyperframes ★57.5k https://github.com/heygen-com/hyperframes
🥉 hypit ★19.6k https://github.com/hypit-ai/hypit
4. lottie ★5.5k https://github.com/diffusionstudio/lottie
5. Remotion skills ★4.9k https://github.com/remotion-dev/skills
6. FireRed-OpenStoryline ★3.5k https://github.com/FireRedTeam/FireRed-OpenStoryline
7. chengfeng-videocut-skills ★3k https://github.com/Agentchengfeng/chengfeng-videocut-skills
8. narrator-ai-cli-skill ★3k https://github.com/NarratorAI-Studio/narrator-ai-cli-skill
9. pixel2motion ★2.4k https://github.com/nolangz/pixel2motion
10. claude-code-video-toolkit ★2.2k https://github.com/digitalsamba/claude-code-video-toolkit

❌ 两个不上榜:
Raven:星数属于整个仓库
remotion-video-skill:安全评级 CAUTION · sudo

📌 排名规则:只收 Agent Skills Hub 安全评级为 SAFE 的项目,按 GitHub 星数排序,每个作者最多两个;星数必须属于这个 skill,仓库主业不是视频的不计名次。数据截至 2026-10-06

章节:
0:00 开场
0:16 Raven 不上榜、第 9 名
0:33 第 8、2 名
0:48 第 10 名、remotion-video-skill 不上榜
1:04 第 4、7 名
1:17 第 6、5 名
1:30 第 3、1 名
1:45 下期预告

你在用哪个做视频?评论区说说👇

#AI做视频 #ClaudeCode #Codex #AI工具 #视频剪辑 #GitHub宝藏项目
```

章节规则:第一条 0:00,至少 3 条,每段不短于 10 秒。上面的时间来自字幕时间轴,都满足。

## 3. 英文标题和描述(字幕 → 添加"英语"→ 标题和说明)

```
AI Video Skills: Top 10 for Claude Code & Codex (SAFE-Graded, 240+ Compared)
```

```
240+ open-source skills let Claude Code, Codex and other agents make videos. Here are the top 10 by GitHub stars, counting only skills graded SAFE.

Full list (240+ skills, each README read and security-graded, filter by type):
https://agentskillshub.top/best/claude-video-skills/?utm_source=youtube&utm_medium=video&utm_campaign=video-top10

Open-source list on GitHub (updated daily):
https://github.com/zhuyansen/awesome-claude-video-skills

1. OpenMontage https://github.com/calesthio/OpenMontage
2. hyperframes https://github.com/heygen-com/hyperframes
3. hypit https://github.com/hypit-ai/hypit
4. lottie https://github.com/diffusionstudio/lottie
5. Remotion skills https://github.com/remotion-dev/skills
6. FireRed-OpenStoryline https://github.com/FireRedTeam/FireRed-OpenStoryline
7. chengfeng-videocut-skills https://github.com/Agentchengfeng/chengfeng-videocut-skills
8. narrator-ai-cli-skill https://github.com/NarratorAI-Studio/narrator-ai-cli-skill
9. pixel2motion https://github.com/nolangz/pixel2motion
10. claude-code-video-toolkit https://github.com/digitalsamba/claude-code-video-toolkit

Left out: Raven (its stars belong to the whole repo) and remotion-video-skill (security scan: CAUTION, uses sudo).

Ranking: only skills graded SAFE by Agent Skills Hub, by GitHub stars, at most two per author; the stars must belong to the skill. Data as of 2026-10-06.

#AIVideo #ClaudeCode #Codex
```

## 4. 字幕

`video-skills-top10.zh.srt` 和 `video-skills-top10.en.srt`,54 条。直接取自视频烧录字幕的时间轴(`codevid/timeline.json` 的 `captions`),文字和时间与画面完全一致;英文是逐条翻译。重新生成:

```
python3 ops/youtube/captions_to_srt.py cues ~/ship2market/sitedata/viral-clone/video-skills-A3/codevid/timeline.json /tmp/cues.json
# 把英文填进每条的 "en" 后存成 ops/youtube/video-skills-top10.cues.json
python3 ops/youtube/captions_to_srt.py srt ops/youtube/video-skills-top10.cues.json ops/youtube/video-skills-top10
```

上传步骤见 `ppt-skills-top10.md` 第 3 节(选视频语言"中文(简体)"→ 上传 `.zh.srt` → 添加英语 → 上传 `.en.srt` → 填英文标题和说明)。

## 5. 其他设置

- **标签**:`ai video skills, claude code video, codex video, openmontage, hyperframes, hypit, remotion skills, lottie, ai video editing, AI做视频, 视频剪辑`
- **分类**:Science & Technology。

## 6. 验收

- 10-13、10-20 用实时 SERP 查 `claude video skills`、`ai video skills`(AIsa `post_dataforseo_serp_google_organic_live`,US/en/desktop,约 $0.025/次)。
- GA 看 `utm_campaign=video-top10` 的会话。
