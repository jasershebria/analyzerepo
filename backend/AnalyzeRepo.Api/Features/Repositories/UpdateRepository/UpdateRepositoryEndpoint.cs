using AnalyzeRepo.Api.Features.Repositories;
using FastEndpoints;
using FluentValidation;
using MediatR;
using Microsoft.EntityFrameworkCore;

namespace AnalyzeRepo.Api.Features.Repositories.UpdateRepository;

public class UpdateRepositoryEndpoint : Endpoint<UpdateRepositoryCommand, UpdateRepositoryResponse>
{
    private readonly IMediator _mediator;

    public UpdateRepositoryEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Put("/repositories/{id}");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Update a repository";
            s.Description = "Updates an existing repository with the provided details";
            s.Response<UpdateRepositoryResponse>(200, "Repository updated successfully");
            s.Response(404, "Repository not found");
            s.Response(400, "Validation failed");
            s.Response(409, "Concurrent modification conflict — refresh and retry");
        });
    }

    public override async Task HandleAsync(UpdateRepositoryCommand req, CancellationToken ct)
    {
        try
        {
            var result = await _mediator.Send(req, ct);
            Response = result;
        }
        catch (KeyNotFoundException)
        {
            HttpContext.Response.StatusCode = 404;
        }
        catch (DbUpdateConcurrencyException)
        {
            HttpContext.Response.StatusCode = 409;
            await HttpContext.Response.WriteAsJsonAsync(
                new { error = "The repository was modified by another request. Please refresh and retry." }, ct);
        }
    }
}

public class UpdateRepositoryValidator : Validator<UpdateRepositoryCommand>
{
    public UpdateRepositoryValidator()
    {
        RuleFor(x => x.Id).NotEmpty();
        RuleFor(x => x.Name).NotEmpty().MaximumLength(200);
        RuleFor(x => x.ProviderId).NotEmpty();
        RuleFor(x => x.WebUrl).NotEmpty().MaximumLength(500)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _)).WithMessage("Web URL must be a valid URL");
    }
}
