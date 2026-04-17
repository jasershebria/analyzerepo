using AnalyzeRepo.Api.Features.Providers.Infrastructure.Plugins;
using FastEndpoints;
using System.Text.Json;

namespace AnalyzeRepo.Api.Features.Repositories.Webhooks.Trigger;

public sealed class WebhookTriggerEndoint : EndpointWithoutRequest
{
    private readonly ProviderResolver _providerResolver;


    public WebhookTriggerEndoint(ProviderResolver providerResolver)
    {
        _providerResolver = providerResolver;
    }

    public override void Configure()
    {
        Post("/webhook/trigger/{name}");
        AllowAnonymous();
        Options(x => x.WithTags("Webhook"));
        Summary(s =>
        {
            s.Summary     = "Receive a Git provider push webhook";
            s.Description = "Parses the payload, builds a ScanJob, and enqueues it for scanning.";
            s.Response(202, "Job accepted and enqueued");
            s.Response(400, "Unknown provider or malformed payload");
        });
    }

    public override async Task HandleAsync(CancellationToken ct)
    {
        var provider = Route<string>("name");

        if (string.IsNullOrWhiteSpace(provider))
        {
            ThrowError("Provider name is required.", 400);
            return;
        }

        JsonElement payload;
        try
        {
            payload = await JsonSerializer.DeserializeAsync<JsonElement>(
                HttpContext.Request.Body, cancellationToken: ct);
        }
        catch (JsonException ex)
        {
            ThrowError($"Request body is not valid JSON: {ex.Message}", 400);
            return;
        }

        ISourceProviderPlugin plugin;
        try
        {
            plugin = _providerResolver.Resolve(provider);
        }
        catch (NotSupportedException ex)
        {
            ThrowError(ex.Message, 400);
            return;
        }

        //var job = await plugin.BuildScanJobAsync(payload);


        HttpContext.Response.StatusCode = 202;
    }
}
