import axios from 'axios';
import { IRepoProviderClient, ProviderAuth, RepoMetadata } from '../interfaces/repo-provider-client.interface';

export class GitLabClient implements IRepoProviderClient {
  private readonly baseUrl: string;

  constructor(apiBaseUrl?: string) {
    this.baseUrl = apiBaseUrl?.replace(/\/$/, '') ?? 'https://gitlab.com/api/v4';
  }

  async getRepoMeta(webUrl: string, auth: ProviderAuth): Promise<RepoMetadata> {
    const match = webUrl.match(/gitlab\.com[/:]([\w.-/]+?)(?:\.git)?$/);
    if (!match) throw new Error(`Cannot parse GitLab URL: ${webUrl}`);
    const encodedPath = encodeURIComponent(match[1]);

    const { data } = await axios.get(`${this.baseUrl}/projects/${encodedPath}`, {
      headers: { 'PRIVATE-TOKEN': auth.token },
    });

    return {
      providerRepoId: String(data.id),
      name: data.path_with_namespace,
      defaultBranch: data.default_branch,
      cloneUrl: data.http_url_to_repo,
    };
  }

  async getBranches(meta: RepoMetadata, auth: ProviderAuth): Promise<string[]> {
    const { data } = await axios.get(
      `${this.baseUrl}/projects/${encodeURIComponent(meta.name)}/repository/branches?per_page=100`,
      { headers: { 'PRIVATE-TOKEN': auth.token } },
    );
    return (data as any[]).map((b) => b.name);
  }
}
