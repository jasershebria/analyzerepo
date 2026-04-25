export interface ProviderAuth {
  authType: number;
  token: string;
}

export interface RepoMetadata {
  providerRepoId: string;
  name: string;
  defaultBranch: string;
  cloneUrl: string;
}

export interface IRepoProviderClient {
  getRepoMeta(webUrl: string, auth: ProviderAuth): Promise<RepoMetadata>;
  getBranches(meta: RepoMetadata, auth: ProviderAuth): Promise<string[]>;
}
