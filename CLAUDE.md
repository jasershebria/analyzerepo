# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Frontend (`frontend/analyezrepo/`)
```bash
npm start          # Dev server on http://localhost:4200
npm run build      # Production build
npm run watch      # Build in watch mode
npm test           # Run unit tests with Vitest
```

### Backend (`backend/AnalyzeRepo.Api/`)
```bash
dotnet run         # Start API on http://localhost:5238
dotnet build       # Build the project
docker-compose up  # Start PostgreSQL (required before dotnet run)
```

## Architecture

### Frontend (Angular 21)

- **Module pattern:** Non-standalone NgModules with `standalone: false` components. Each feature is a lazy-loaded module declared in `app-routing.module.ts`. `SharedModule` (`src/app/shared/shared.module.ts`) re-exports `CommonModule`, `FormsModule`, `ReactiveFormsModule`, and all Lucide icons — import `SharedModule` in every feature module instead of individual Angular modules.
- **State:** Angular signals (`signal`, `computed`, `effect`) — no NgRx. Feature-scoped services (provided in their module, not `root`) hold signal-based state.
- **HTTP:** `RepositoryService` and `ProviderService` live under `features/settings/tabs/.../services/` but are `providedIn: 'root'` and reused across features. All API calls use `${environment.apiBase}/api/...`.
- **Styling:** SCSS with design tokens in `src/app/_variables.scss`. Bootstrap 5 grid only (no Bootstrap components). Dark theme with indigo/purple accents (`#6366F1`, `#7C3AED`).
- **Icons:** Lucide via `lucide-angular`. Icons must be registered in `SharedModule` before use.

### Backend (.NET 9)

- **Endpoint pattern:** Every endpoint follows `FastEndpoints → MediatR handler`. Files are co-located per feature under `Features/{Domain}/{Operation}/`:
  - `*Endpoint.cs` — FastEndpoints class, configures route and calls `_mediator.Send(req)`
  - `*Handler.cs` — MediatR `IRequestHandler<TRequest, TResponse>` with business logic
  - `*Models.cs` (or `*Modal.cs`) — all request/response records for the domain in one file

- **Pipeline behaviors** (applied to all MediatR requests):
  1. `LoggingBehavior` — logs request/response
  2. `ValidationBehavior` — runs FluentValidation; validators are co-located as `*Validator : Validator<TRequest>` in the endpoint file

- **Pagination:** `PagedResult<T>` (`{ totalCount, items }`) is the standard paged response. Queries implement `IPaginationFilter` for `PageIndex`, `SkipCount`, `MaxResultCount`.

- **Domain base classes** (`Common/`): `Entity<TId>`, `AggregateRoot<TId>`, `AuditedAggregateRoot` (adds `CreatedAt`/`UpdatedAt`), `FullAuditedAggregateRoot` (adds `IsDeleted` soft-delete).

- **AI:** Semantic Kernel with `AnthropicChatCompletionService` (claude-opus-4-7 in dev). AI config lives in `appsettings.Development.json` under `"Anthropic"`. Chat endpoint is at `POST /api/ai/chat`.

- **Database:** PostgreSQL via EF Core 9. Migrations auto-applied on startup. Dev connection: `Host=localhost;Port=5432;Database=analyzerepo;Username=postgres;Password=postgres`.

### Frontend ↔ Backend
- Dev: frontend `http://localhost:4200` → backend `http://localhost:5238/api/...`
- CORS in `Program.cs` whitelists `http://localhost:4200`
- Models shared between Angular and backend are mirrored in `src/app/models/analysis.models.ts`
