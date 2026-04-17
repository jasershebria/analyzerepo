using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Repositories.Domain;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.CreateRepository;

public class CreateRepositoryHandler : IRequestHandler<CreateRepositoryCommand, CreateRepositoryResponse>
{
    private readonly ApplicationDbContext _context;

    public CreateRepositoryHandler(ApplicationDbContext context) => _context = context;

    public async Task<CreateRepositoryResponse> Handle(CreateRepositoryCommand request, CancellationToken cancellationToken)
    {
        var providerExists = await _context.SourceProviders
            .AnyAsync(p => p.Id == request.ProviderId && p.IsActive, cancellationToken);

        if (!providerExists)
            throw new InvalidOperationException($"Provider with ID '{request.ProviderId}' not found or is inactive.");

        var existingRepo = await _context.Repositories
            .AnyAsync(r => r.ProviderId == request.ProviderId && r.ProviderRepoId == request.ProviderRepoId, cancellationToken);

        if (existingRepo)
            throw new InvalidOperationException($"Repository '{request.Name}' already exists for this provider.");

        var repository = Repository.Create(
            name:          request.Name,
            providerId:    request.ProviderId,
            webUrl:        request.WebUrl,
            providerRepoId: request.ProviderRepoId,
            cloneUrl:      request.CloneUrl,
            defaultBranch: request.DefaultBranch,
            authType:      request.AuthenticationType,
            secretRef:     request.SecretRef,
            branchRules:   request.BranchRules.Select(r => (r.Pattern, r.ScanOnPush)),
            runInitialScan: request.RunInitialScan
        );

        _context.Repositories.Add(repository);
        await _context.SaveChangesAsync(cancellationToken);

        return new CreateRepositoryResponse
        {
            Id         = repository.Id,
            Name       = repository.Name,
            ProviderId = repository.ProviderId,
            WebUrl     = repository.WebUrl,
            CreatedAt  = repository.CreatedAt
        };
    }
}
