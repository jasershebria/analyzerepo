using FastEndpoints;
using FluentValidation;
using MediatR;

namespace AnalyzeRepo.Api.Features.Repository.ConnectRepository;

public class ConnectRepositoryEndpoint(IMediator mediator)
    : Endpoint<ConnectRepositoryCommand, ConnectRepositoryResponse>
{
    public override void Configure()
    {
        Post("/repositories/connect");
        AllowAnonymous();
        Options(x => x.WithTags("Repository"));
        Summary(s =>
        {
            s.Summary     = "Connect to a GitHub repository";
            s.Description = "Validates the token and stores the connection";
            s.Response<ConnectRepositoryResponse>(200, "Connected");
            s.Response(400, "Validation failed");
            s.Response(422, "Cannot reach repository");
        });
    }

    public override async Task HandleAsync(ConnectRepositoryCommand req, CancellationToken ct)
    {
        var result = await mediator.Send(req, ct);
        await SendOkAsync(result, ct);
    }
}

public class ConnectRepositoryValidator : Validator<ConnectRepositoryCommand>
{
    public ConnectRepositoryValidator()
    {
        RuleFor(x => x.RepoUrl)
            .NotEmpty().WithMessage("Repository URL is required.")
            .Must(u => Uri.TryCreate(u, UriKind.Absolute, out _))
            .WithMessage("Must be a valid URL.");

        RuleFor(x => x.Token)
            .NotEmpty().WithMessage("GitHub token is required.");
    }
}
