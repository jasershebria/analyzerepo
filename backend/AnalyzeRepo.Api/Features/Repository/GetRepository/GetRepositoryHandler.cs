using AnalyzeRepo.Api.Data.Application.Exceptions;
using AnalyzeRepo.Api.Data.Infrastructure;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repository.GetRepository;

public class GetRepositoryHandler(AppDbContext db)
    : IRequestHandler<GetRepositoryQuery, GetRepositoryResponse>
{
    public async Task<GetRepositoryResponse> Handle(GetRepositoryQuery req, CancellationToken ct)
    {
        var conn = await db.RepoConnections
            .AsNoTracking()
            .FirstOrDefaultAsync(r => r.Id == req.Id, ct)
            ?? throw new NotFoundException(nameof(Domain.RepoConnection), req.Id);

        return new GetRepositoryResponse(
            conn.Id, conn.RepoUrl, conn.Owner,
            conn.RepoName, conn.IsConnected, conn.CreatedAt);
    }
}
