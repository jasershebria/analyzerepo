using AnalyzeRepo.Api.Data.Infrastructure;
using AnalyzeRepo.Api.Features.Providers.Domain;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Providers.CreateProvider;

public class CreateProviderHandler : IRequestHandler<CreateProviderCommand, ProviderDto>
{
    private readonly ApplicationDbContext _context;

    public CreateProviderHandler(ApplicationDbContext context) => _context = context;

    public async Task<ProviderDto> Handle(CreateProviderCommand request, CancellationToken cancellationToken)
    {
        var codeExists = await _context.SourceProviders
            .AnyAsync(p => p.Code == request.Code.ToLowerInvariant() && !p.IsDeleted, cancellationToken);

        if (codeExists)
            throw new InvalidOperationException($"A provider with code '{request.Code}' already exists.");

        var provider = SourceProvider.Create(request.Name, request.Code, request.ApiBaseUrl);

        _context.SourceProviders.Add(provider);
        await _context.SaveChangesAsync(cancellationToken);

        return new ProviderDto
        {
            Id         = provider.Id,
            Name       = provider.Name,
            Code       = provider.Code,
            ApiBaseUrl = provider.ApiBaseUrl,
            IsActive   = provider.IsActive,
            CreatedAt  = provider.CreatedAt,
        };
    }
}
