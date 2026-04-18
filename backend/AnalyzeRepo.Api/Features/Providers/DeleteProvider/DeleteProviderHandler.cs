using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Providers.DeleteProvider;

public class DeleteProviderHandler : IRequestHandler<DeleteProviderCommand, Unit>
{
    private readonly ApplicationDbContext _context;

    public DeleteProviderHandler(ApplicationDbContext context) => _context = context;

    public async Task<Unit> Handle(DeleteProviderCommand request, CancellationToken cancellationToken)
    {
        var provider = await _context.SourceProviders
            .FirstOrDefaultAsync(p => p.Id == request.Id && !p.IsDeleted, cancellationToken);

        if (provider is null)
            throw new InvalidOperationException($"Provider '{request.Id}' not found.");

        provider.Delete();
        await _context.SaveChangesAsync(cancellationToken);

        return Unit.Value;
    }
}
