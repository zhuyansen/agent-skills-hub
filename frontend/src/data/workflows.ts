export interface WorkflowStep {
  name: string;
  repo: string;
  description_zh: string;
  description_en: string;
}

export interface Workflow {
  id: string;
  icon: string;
  title_zh: string;
  title_en: string;
  description_zh: string;
  description_en: string;
  steps: WorkflowStep[];
}

export const workflows: Workflow[] = [
  {
    id: "social-media",
    icon: "share",
    title_zh: "自媒体内容创作",
    title_en: "Social Media Content",
    description_zh: "从内容创作到多平台发布的完整工作流",
    description_en: "End-to-end workflow from content creation to multi-platform publishing",
    steps: [
      {
        name: "Agent-Reach",
        repo: "https://github.com/Panniantong/Agent-Reach",
        description_zh: "阅读 X (Twitter) 内容",
        description_en: "Read X (Twitter) content",
      },
      {
        name: "baoyu-skills",
        repo: "https://github.com/JimLiu/baoyu-skills",
        description_zh: "封面图 + 微信公众号 + 小红书图文",
        description_en: "Cover images + WeChat + Xiaohongshu posts",
      },
      {
        name: "qiaomu-x-article-publisher",
        repo: "https://github.com/joeseesun/qiaomu-x-article-publisher",
        description_zh: "Markdown 发布 X 长文",
        description_en: "Publish long-form articles to X",
      },
    ],
  },
  {
    id: "learning",
    icon: "book",
    title_zh: "学习研究",
    title_en: "Learning & Research",
    description_zh: "高效获取和整理知识的学习工作流",
    description_en: "Efficient knowledge acquisition and organization workflow",
    steps: [
      {
        name: "yt-search-download",
        repo: "https://github.com/joeseesun/yt-search-download",
        description_zh: "YouTube 内容搜索与下载",
        description_en: "YouTube content search & download",
      },
      {
        name: "anything-to-notebooklm",
        repo: "https://github.com/joeseesun/anything-to-notebooklm",
        description_zh: "任意内容转换到 NotebookLM",
        description_en: "Convert any content to NotebookLM",
      },
      {
        name: "defuddle-skill",
        repo: "https://github.com/joeseesun/defuddle-skill",
        description_zh: "网页内容智能提取",
        description_en: "Smart web content extraction",
      },
    ],
  },
  {
    id: "dev-tools",
    icon: "wrench",
    title_zh: "开发者工具",
    title_en: "Developer Tools",
    description_zh: "提升开发效率的实用工具集",
    description_en: "Practical tools to boost developer productivity",
    steps: [
      {
        name: "knowledge-site-creator",
        repo: "https://github.com/joeseesun/knowledge-site-creator",
        description_zh: "知识站点一键生成",
        description_en: "One-click knowledge site generator",
      },
      {
        name: "qiaomu-design-advisor",
        repo: "https://github.com/joeseesun/qiaomu-design-advisor",
        description_zh: "UI/UX 设计顾问",
        description_en: "UI/UX design advisor",
      },
      {
        name: "skill-publisher",
        repo: "https://github.com/joeseesun/skill-publisher",
        description_zh: "Skill 发布与管理工具",
        description_en: "Skill publishing & management tool",
      },
      {
        name: "qiaomu-music-player-spotify",
        repo: "https://github.com/joeseesun/qiaomu-music-player-spotify",
        description_zh: "Spotify 音乐播放器",
        description_en: "Spotify music player",
      },
    ],
  },
];
