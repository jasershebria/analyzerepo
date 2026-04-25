import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Repository } from './entities/repository.entity';
import { RepositoryAuth } from './entities/repository-auth.entity';
import { BranchTrackingRule } from './entities/branch-tracking-rule.entity';
import { SourceProvider } from '../providers/entities/source-provider.entity';
import { RepositoriesController } from './repositories.controller';
import { RepositoriesService } from './repositories.service';
import { RepoSyncService } from './repo-sync.service';
import { ProviderClientsModule } from '../provider-clients/provider-clients.module';

@Module({
  imports: [
    TypeOrmModule.forFeature([Repository, RepositoryAuth, BranchTrackingRule, SourceProvider]),
    ProviderClientsModule,
  ],
  controllers: [RepositoriesController],
  providers: [RepositoriesService, RepoSyncService],
  exports: [RepositoriesService, RepoSyncService],
})
export class RepositoriesModule {}
