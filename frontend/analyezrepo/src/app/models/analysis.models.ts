export interface ProviderDto {
  id: string;
  name: string;
  code: string;
  apiBaseUrl: string;
  isActive: boolean;
  createdAt: string;
}

export interface TestConnectionRequest {
  providerId: string;
  webUrl: string;
  authType: string;
  secretRefOrToken: string;
}

export interface TestConnectionResponse {
  success: boolean;
  repoName?: string;
  providerRepoId?: string;
  providerWorkspaceId?: string;
  defaultBranch?: string;
  cloneUrl?: string;
  webUrlNormalized?: string;
  errorMessage?: string;
  branches: { name: string }[];
}

export interface CreateProviderCommand {
  name: string;
  code: string;
  apiBaseUrl: string;
}

export interface CreateRepositoryCommand {
  providerId: string;
  providerRepoId: string;
  name: string;
  webUrl: string;
  cloneUrl: string;
  defaultBranch: string;
  authenticationType: number;
  secretRef: string;
  runInitialScan: boolean;
  branchRules: { pattern: string; scanOnPush: boolean }[];
}

export interface CreateRepositoryResponse {
  id: string;
  name: string;
  providerId: string;
  webUrl: string;
  createdAt: string;
}

export interface Repository {
  id: string;
  name: string;
  url: string;
  token?: string;
  addedAt: string;
}

export interface RepositoryDto {
  id: string;
  name: string;
  webUrl: string;
  createdAt: string;
}

export interface PagedResult<T> {
  totalCount: number;
  items: T[];
}

export interface AiChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface AiChatHistoryRequest {
  messages: AiChatMessage[];
  systemPrompt?: string;
  repoId?: string;
}

export interface AiChatResponse {
  reply: string;
}

export interface BranchRuleDto {
  id: string;
  pattern: string;
  scanOnPush: boolean;
  isEnabled: boolean;
}

export interface GetRepositoryResponse {
  id: string;
  name: string;
  providerId: string;
  webUrl: string;
  cloneUrl: string;
  defaultBranch: string;
  providerRepoId?: string;
  providerWorkspaceId?: string;
  isActive: boolean;
  lastSeenAtUtc?: string;
  createdAt: string;
  updatedAt?: string;
  isDeleted: boolean;
  authenticationType?: number;
  secretRef?: string;
  branchRules: BranchRuleDto[];
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
