import axios from 'axios';
import { IRepoProviderClient, ProviderAuth, RepoMetadata } from '../interfaces/repo-provider-client.interface';

export class GitHubClient implements IRepoProviderClient {
  private readonly baseUrl: string;

  constructor(apiBaseUrl?: string) {
    this.baseUrl = apiBaseUrl?.replace(/\/$/, '') ?? 'https://api.github.com';
  }

  async getRepoMeta(webUrl: string, auth: ProviderAuth): Promise<RepoMetadata> {
    const match = webUrl.match(/github\.com[/:]([\w.-]+)\/([\w.-]+?)(?:\.git)?$/);
    if (!match) throw new Error(`Cannot parse GitHub URL: ${webUrl}`);
    const [, owner, repo] = match;

    const { data } = await axios.get(`${this.baseUrl}/repos/${owner}/${repo}`, {
      headers: { Authorization: `token ${auth.token}`, Accept: 'application/vnd.github+json' },
    });

    return {
      providerRepoId: String(data.id),
      name: data.full_name,
      defaultBranch: data.default_branch,
      cloneUrl: data.clone_url,
    };
  }

  async getBranches(meta: RepoMetadata, auth: ProviderAuth): Promise<string[]> {
    const { data } = await axios.get(
      `${this.baseUrl}/repos/${meta.name}/branches?per_page=100`,
      { headers: { Authorization: `token ${auth.token}`, Accept: 'application/vnd.github+json' } },
    );
    return (data as any[]).map((b) => b.name);
  }
}
