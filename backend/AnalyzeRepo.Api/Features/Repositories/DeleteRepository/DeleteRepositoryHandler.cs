using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.DeleteRepository;

public class DeleteRepositoryHandler : IRequestHandler<DeleteRepositoryCommand, Unit>
{
    private readonly ApplicationDbContext _context;

    public DeleteRepositoryHandler(ApplicationDbContext context) => _context = context;

    public async Task<Unit> Handle(DeleteRepositoryCommand request, CancellationToken cancellationToken)
    {
        var repository = await _context.Repositories
            .Include(r => r.BranchRules)
            .Include(r => r.Auth)
            .FirstOrDefaultAsync(r => r.Id == request.Id, cancellationToken);

        if (repository == null)
            throw new KeyNotFoundException($"Repository with ID {request.Id} not found");

        _context.Repositories.Remove(repository);
        await _context.SaveChangesAsync(cancellationToken);

        return Unit.Value;
    }
}
