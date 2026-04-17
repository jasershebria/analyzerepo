using AnalyzeRepo.Api.Features.Repositories;
using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repositories.CreateRepository;

public class CreateRepositoryEndpoint : Endpoint<CreateRepositoryCommand, CreateRepositoryResponse>
{
    private readonly IMediator _mediator;

    public CreateRepositoryEndpoint(IMediator mediator) => _mediator = mediator;

    public override void Configure()
    {
        Post("/repositories");
        AllowAnonymous();
        Options(x => x.WithTags("Repositories"));
        Summary(s =>
        {
            s.Summary = "Create a new repository";
            s.Description = "Creates a new repository with the provided details";
            s.Response<CreateRepositoryResponse>(201, "Repository created successfully");
            s.Response(400, "Validation failed");
        });
    }

    public override async Task HandleAsync(CreateRepositoryCommand req, CancellationToken ct)
    {
        var result = await _mediator.Send(req, ct);
        Response = result;
        HttpContext.Response.StatusCode = 201;
    }
}

public class CreateRepositoryValidator : Validator<CreateRepositoryCommand>
{
    public CreateRepositoryValidator()
    {
        RuleFor(x => x.Name).NotEmpty().MaximumLength(200);
        RuleFor(x => x.ProviderId).NotEmpty();
        RuleFor(x => x.ProviderRepoId).NotEmpty().MaximumLength(200);
        RuleFor(x => x.WebUrl).NotEmpty().MaximumLength(500)
            .Must(url => Uri.TryCreate(url, UriKind.Absolute, out _)).WithMessage("Web URL must be a valid URL");
        RuleFor(x => x.CloneUrl).NotEmpty().MaximumLength(500);
        RuleFor(x => x.DefaultBranch).NotEmpty().MaximumLength(100);
        RuleFor(x => x.AuthenticationType).IsInEnum();
        RuleFor(x => x.SecretRef).NotEmpty().MaximumLength(500);
        RuleFor(x => x.BranchRules).NotEmpty().WithMessage("At least one branch rule is required");
        RuleForEach(x => x.BranchRules).ChildRules(rule =>
        {
            rule.RuleFor(r => r.Pattern).NotEmpty().MaximumLength(200);
        });
    }
}
