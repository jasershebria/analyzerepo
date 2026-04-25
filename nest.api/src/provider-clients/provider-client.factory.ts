import { Injectable } from '@nestjs/common';
import { IRepoProviderClient } from './interfaces/repo-provider-client.interface';
import { GitHubClient } from './clients/github.client';
import { GitLabClient } from './clients/gitlab.client';
import { BitbucketClient } from './clients/bitbucket.client';

@Injectable()
export class ProviderClientFactory {
  getClient(providerCode: string, apiBaseUrl?: string): IRepoProviderClient {
    switch (providerCode.toLowerCase()) {
      case 'github': return new GitHubClient(apiBaseUrl);
      case 'gitlab': return new GitLabClient(apiBaseUrl);
      case 'bitbucket': return new BitbucketClient(apiBaseUrl);
      default: throw new Error(`Provider '${providerCode}' is not supported.`);
    }
  }
}
