import axios from 'axios';
import { IRepoProviderClient, ProviderAuth, RepoMetadata } from '../interfaces/repo-provider-client.interface';

export class BitbucketClient implements IRepoProviderClient {
  private readonly baseUrl: string;

  constructor(apiBaseUrl?: string) {
    this.baseUrl = apiBaseUrl?.replace(/\/$/, '') ?? 'https://api.bitbucket.org/2.0';
  }

  async getRepoMeta(webUrl: string, auth: ProviderAuth): Promise<RepoMetadata> {
    const match = webUrl.match(/bitbucket\.org[/:]([\w.-]+)\/([\w.-]+?)(?:\.git)?$/);
    if (!match) throw new Error(`Cannot parse Bitbucket URL: ${webUrl}`);
    const [, workspace, slug] = match;

    const { data } = await axios.get(`${this.baseUrl}/repositories/${workspace}/${slug}`, {
      headers: { Authorization: `Bearer ${auth.token}` },
    });

    return {
      providerRepoId: data.uuid,
      name: data.full_name,
      defaultBranch: data.mainbranch?.name ?? 'main',
      cloneUrl: (data.links?.clone as any[])?.find((l) => l.name === 'https')?.href ?? webUrl,
    };
  }

  async getBranches(meta: RepoMetadata, auth: ProviderAuth): Promise<string[]> {
    const { data } = await axios.get(
      `${this.baseUrl}/repositories/${meta.name}/refs/branches?pagelen=100`,
      { headers: { Authorization: `Bearer ${auth.token}` } },
    );
    return ((data.values ?? []) as any[]).map((b) => b.name);
  }
}
