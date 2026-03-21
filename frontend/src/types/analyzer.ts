export interface LLMFinding {
  severity: "high" | "medium" | "low";
  description: string;
  mitigation?: string;
}

export interface LLMAnalysis {
  grade: string;
  confidence: number;
  risk_summary: string;
  findings: LLMFinding[];
  recommendation: string;
}

export interface AnalyzerSecurity {
  rule_grade: string;
  llm_grade: string | null;
  final_grade: string;
  flags: string[];
  llm_analysis: LLMAnalysis | null;
}

export interface AnalyzerRepo {
  full_name: string;
  stars: number;
  description: string;
  license: string | null;
  category: string | null;
  repo_url: string;
}

export interface AnalyzerQuality {
  score: number;
  completeness: number;
  clarity: number;
  specificity: number;
  examples: number;
  agent_readiness: number;
}

export interface AnalyzerResult {
  repo: AnalyzerRepo;
  indexed: boolean;
  security: AnalyzerSecurity;
  quality: AnalyzerQuality | null;
}
