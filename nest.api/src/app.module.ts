import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { MongooseModule } from '@nestjs/mongoose';
import { configuration } from './config/configuration';
import { typeOrmConfig } from './database/typeorm.config';
import { mongooseConfig } from './database/mongoose.config';
import { ProvidersModule } from './providers/providers.module';
import { RepositoriesModule } from './repositories/repositories.module';
import { ProviderClientsModule } from './provider-clients/provider-clients.module';
import { AiModule } from './ai/ai.module';
import { ToolsModule } from './tools/tools.module';
import { AgentModule } from './agent/agent.module';
import { RagModule } from './rag/rag.module';
import { WebhooksModule } from './webhooks/webhooks.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true, load: [configuration], envFilePath: '.env' }),
    TypeOrmModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => typeOrmConfig(config),
    }),
    MongooseModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => mongooseConfig(config),
    }),
    ProvidersModule,
    RepositoriesModule,
    ProviderClientsModule,
    AiModule,
    ToolsModule,
    AgentModule,
    RagModule,
    WebhooksModule,
    HealthModule,
  ],
})
export class AppModule {}
