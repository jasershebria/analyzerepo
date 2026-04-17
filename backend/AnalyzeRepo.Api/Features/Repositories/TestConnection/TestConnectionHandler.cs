using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Providers.Domain;
using AnalyzeRepo.Api.Features.Providers.Infrastructure.ProviderClients;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.TestConnection;

public class TestConnectionHandler : IRequestHandler<TestConnectionCommand, TestConnectionResponse>
{
    private readonly ApplicationDbContext      _context;
    private readonly RepoProviderClientFactory _providerFactory;
    private readonly ILogger<TestConnectionHandler> _logger;

    public TestConnectionHandler(
        ApplicationDbContext context,
        RepoProviderClientFactory providerFactory,
        ILogger<TestConnectionHandler> logger)
    {
        _context         = context;
        _providerFactory = providerFactory;
        _logger          = logger;
    }

    public async Task<TestConnectionResponse> Handle(TestConnectionCommand request, CancellationToken cancellationToken)
    {
        try
        {
            var provider = await _context.SourceProviders
                .FirstOrDefaultAsync(p => p.Id == request.ProviderId && p.IsActive, cancellationToken);

            if (provider == null)
                return Fail("Provider not found or inactive");

            var providerClient = _providerFactory.GetClient(provider.Code, provider.ApiBaseUrl);
            var auth           = new ProviderAuth(request.AuthType, request.SecretRefOrToken);
            var repoMeta       = await providerClient.GetRepoMetaAsync(request.WebUrl, auth, cancellationToken);
            var branches       = await providerClient.GetBranchesAsync(repoMeta, auth, cancellationToken);

            _logger.LogInformation("Test connection successful for {RepoName} on {Provider}", repoMeta.Name, provider.Code);

            return new TestConnectionResponse(
                Success:             true,
                RepoName:            repoMeta.Name,
                ProviderRepoId:      repoMeta.ProviderRepoId,
                ProviderWorkspaceId: repoMeta.ProviderWorkspaceId,
                DefaultBranch:       repoMeta.DefaultBranch,
                CloneUrl:            repoMeta.CloneUrl,
                WebUrlNormalized:    repoMeta.WebUrlNormalized,
                ErrorMessage:        null,
                Branches:            branches.Select(b => new GitHubBranch { Name = b }).ToList()
            );
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Test connection failed for {WebUrl}", request.WebUrl);
            return Fail(ex.Message);
        }
    }

    private static TestConnectionResponse Fail(string message) =>
        new(false, null, null, null, null, null, null, message, new List<GitHubBranch>());
}
