# YouTube 元数据:让 AI 做 PPT 的 200+ 个 Skill,星数前十

视频:https://www.youtube.com/watch?v=T0keDFpa5i8(2026-10-06 发布,2 分 04 秒,中文)

发布时:描述为空、没有标签、没有字幕,分类是 People & Blogs。目标搜索词 `ppt skills`(美国 Google 第一页有 2 个 YouTube 位,AI 概览引用了 3 个 YouTube 视频)是英文的,所以要补英文标题和描述的翻译。

## 1. 中文描述(默认语言)

排名按视频口播(转写见 `ppt-skills-top10.zh.srt`)。

```
200 多个让 AI 做 PPT 的开源 Skill,挑出最值得装的前十。

完整榜单(203 个,逐个读过 README、做了安全评级,可按类型筛选):
https://agentskillshub.top/best/ppt-presentation/?utm_source=youtube&utm_medium=video&utm_campaign=ppt-top10

GitHub 开源合集(每天自动更新):
https://github.com/zhuyansen/awesome-codex-ppt-skills

前十:
1. ppt-master https://github.com/hugohe3/ppt-master
2. frontend-slides https://github.com/zarazhangrui/frontend-slides
3. guizang-ppt-skill https://github.com/op7418/guizang-ppt-skill
4. dashi-ppt-skill https://github.com/chuspeeism/dashi-ppt-skill
5. html-ppt-skill https://github.com/lewislulu/html-ppt-skill
6. codex-ppt-skill https://github.com/ningzimu/codex-ppt-skill
7. PPTAgent https://github.com/icip-cas/PPTAgent
8. GordenPPTSkill https://github.com/GordenSun/GordenPPTSkill
9. image-to-editable-ppt-skill https://github.com/ningzimu/image-to-editable-ppt-skill
10. GordenSuperPPTSkills https://github.com/GordenSun/GordenSuperPPTSkills

不上榜:GPT-Image2-Skill(图片提示词库,不是做 PPT 的)、NanoBanana-PPT-Skills(安全扫描 Caution:用了 sudo)。

章节:
0:00 开场
0:16 第 7、8 名(GPT-Image2-Skill 不上榜)
0:36 第 2、10 名
0:53 第 4 名(NanoBanana 不上榜)
1:07 第 6、9 名
1:22 第 5、3 名
1:35 第 1 名 ppt-master

#PPTSkills #ClaudeCode #Codex #AIPPT
```

章节规则:第一条必须是 0:00,至少 3 条,每段不短于 10 秒(上面都满足)。

## 2. 英文标题和描述(YouTube Studio → 字幕 → 语言 → 添加"英语"→ 标题和说明)

标题(≤70 字符,核心词放最前):

```
PPT Skills: Top 10 AI PPT Skills for Claude Code & Codex (by Stars)
```

描述:

```
Top 10 open-source PPT skills for Claude Code and Codex, picked by GitHub stars from 200+.

Full list (203 skills, each README read and security-graded, filter by type):
https://agentskillshub.top/best/ppt-presentation/?utm_source=youtube&utm_medium=video&utm_campaign=ppt-top10

Open-source list on GitHub (updated daily):
https://github.com/zhuyansen/awesome-codex-ppt-skills

Top 10:
1. ppt-master https://github.com/hugohe3/ppt-master
2. frontend-slides https://github.com/zarazhangrui/frontend-slides
3. guizang-ppt-skill https://github.com/op7418/guizang-ppt-skill
4. dashi-ppt-skill https://github.com/chuspeeism/dashi-ppt-skill
5. html-ppt-skill https://github.com/lewislulu/html-ppt-skill
6. codex-ppt-skill https://github.com/ningzimu/codex-ppt-skill
7. PPTAgent https://github.com/icip-cas/PPTAgent
8. GordenPPTSkill https://github.com/GordenSun/GordenPPTSkill
9. image-to-editable-ppt-skill https://github.com/ningzimu/image-to-editable-ppt-skill
10. GordenSuperPPTSkills https://github.com/GordenSun/GordenSuperPPTSkills

Left out: GPT-Image2-Skill (an image-prompt library, not a PPT tool) and NanoBanana-PPT-Skills (security scan: Caution, uses sudo).

#PPTSkills #ClaudeCode #Codex #AIPPT
```

## 3. 其他设置

- **字幕**:两份已备好,`ops/youtube/ppt-skills-top10.zh.srt`(中文)和 `ppt-skills-top10.en.srt`(英文),54 条,直接取自视频烧录字幕的时间轴(`~/ship2market/sitedata/viral-clone/ppt-skills-A3/codevid/timeline.json`,用 `captions_to_srt.py` 转),文字和时间与画面一致;英文逐条翻译(`ppt-skills-top10.cues.json`)。10-06 第一版是 Whisper 转写的 30 条,已替换。上传步骤:
  1. YouTube Studio → 左侧"字幕" → 点这条视频。
  2. 第一次会让你选视频语言:选"中文(简体)"。
  3. 中文那一行 → 字幕 → "添加" → "上传文件" → 选"包含时间" → 选 `.zh.srt` → 发布。
  4. 页面上方"添加语言" → 英语;英语那一行 → 字幕 → "添加" → "上传文件" → "包含时间" → 选 `.en.srt` → 发布。
  5. 英语那一行的"标题和说明"列 → "添加" → 粘贴第 2 节的英文标题和描述 → 发布。
  6. 视频画面里已经烧录了中文字幕;上传的字幕默认关闭,观众开 CC 才显示,不会和画面重叠。它的作用是让 YouTube 和 Google 读到视频内容。
- **标签**:`ppt skills, ppt skill, ai ppt, claude code ppt, codex ppt skill, ppt master, guizang ppt skill, frontend slides, ai presentation, 做PPT, AI做PPT`
- **分类**:Science & Technology。
- **章节**:已写在第 1 节中文描述末尾(时间来自字幕);英文描述想加的话照抄时间,标题译成英文。Google 会在搜索结果里显示章节。

## 4. 验收

- 10-13、10-20 用实时 SERP 查 `ppt skills`(AIsa `post_dataforseo_serp_google_organic_live`,US/en/desktop,约 $0.025/次):视频是否进 YouTube 位或 AI 概览引用。
- GA 看 `utm_source=youtube` 的会话。
