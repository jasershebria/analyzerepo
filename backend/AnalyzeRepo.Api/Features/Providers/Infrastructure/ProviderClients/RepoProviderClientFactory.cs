namespace AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;


public class RepoProviderClientFactory
{
    private readonly IServiceProvider _serviceProvider;

    public RepoProviderClientFactory(IServiceProvider serviceProvider)
    {
        _serviceProvider = serviceProvider;
    }

    public IRepoProviderClient GetClient(string providerCode, string? apiBaseUrl = null)
    {
        switch (providerCode.ToLowerInvariant())
        {
            case "github":
                var client = _serviceProvider.GetRequiredService<GitHubRepoProviderClient>();
                client.Configure(apiBaseUrl);
                return client;
            case "bitbucket":
                var bbClient = _serviceProvider.GetRequiredService<BitbucketRepoProviderClient>();
                bbClient.Configure(apiBaseUrl);
                return bbClient;
            case "gitlab":
                var glClient = _serviceProvider.GetRequiredService<GitLabRepoProviderClient>();
                glClient.Configure(apiBaseUrl);
                return glClient;
            default:
                throw new NotSupportedException($"Provider '{providerCode}' is not supported");
        }
    }
}
