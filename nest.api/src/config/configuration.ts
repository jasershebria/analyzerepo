export const configuration = () => ({
  port: parseInt(process.env.PORT ?? '3000', 10),
  database: {
    url: process.env.DATABASE_URL ?? 'postgresql://postgres:postgres@localhost:5432/analyzerepo',
  },
  ai: {
    baseUrl: process.env.AI_BASE_URL ?? 'https://api.anthropic.com',
    apiKey: process.env.AI_API_KEY ?? '',
    model: process.env.AI_MODEL ?? 'claude-sonnet-4-6',
    maxThinkingTokens: parseInt(process.env.MAX_THINKING_TOKENS ?? '0', 10),
  },
  mongodb: {
    url: process.env.MONGODB_URL ?? 'mongodb://admin:admin123@localhost:27017',
    db: process.env.MONGODB_DB ?? 'analyzerepo_rag',
  },
  embedding: {
    model: process.env.EMBEDDING_MODEL ?? 'nomic-embed-text',
    baseUrl: process.env.EMBEDDING_BASE_URL ?? 'http://localhost:11434',
  },
  git: {
    cloneBasePath: process.env.GIT_CLONE_BASE_PATH ?? 'D:\\repos',
  },
  corsOrigins: (process.env.CORS_ORIGINS ?? 'http://localhost:4200').split(','),
});
