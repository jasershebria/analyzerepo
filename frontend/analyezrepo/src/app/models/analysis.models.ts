export interface Repository {
  id: string;
  name: string;
  url: string;
  token?: string;
  addedAt: string;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface AnalysisStep {
  number: number;
  title: string;
  frontendComponent: string;
  userAction: string;
  apiEndpoint: string;
  backendMethod: string;
}

export interface CodeReference {
  file: string;
  snippet: string;
}

export interface AnalysisData {
  steps: AnalysisStep[];
  mermaidCode: string;
  codeReferences: CodeReference[];
}

export interface HistoryItem {
  id: number;
  name: string;
  repo: string;
  date: string;
  time: string;
  flows: number;
  queries: number;
}

export interface StatCard {
  label: string;
  value: string;
  iconName: string;
  change: string;
  gradientFrom: string;
  gradientTo: string;
}

export interface RecentAnalysis {
  name: string;
  repo: string;
  date: string;
  flows: number;
}
