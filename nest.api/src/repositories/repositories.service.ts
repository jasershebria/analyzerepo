import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ILike, Repository as TypeOrmRepo } from 'typeorm';
import { Repository } from './entities/repository.entity';
import { RepositoryAuth } from './entities/repository-auth.entity';
import { BranchTrackingRule } from './entities/branch-tracking-rule.entity';
import { SourceProvider } from '../providers/entities/source-provider.entity';
import {
  CreateRepositoryDto,
  GetAllRepositoriesQuery,
  GetRepositoryResponse,
  RepositoryDto,
  TestConnectionDto,
  TestConnectionResponse,
  UpdateRepositoryDto,
} from './dto/repository.dto';
import { PagedResult } from '../common/dto/paged-result.dto';
import { ProviderClientFactory } from '../provider-clients/provider-client.factory';

@Injectable()
export class RepositoriesService {
  constructor(
    @InjectRepository(Repository) private readonly repo: TypeOrmRepo<Repository>,
    @InjectRepository(RepositoryAuth) private readonly authRepo: TypeOrmRepo<RepositoryAuth>,
    @InjectRepository(BranchTrackingRule) private readonly ruleRepo: TypeOrmRepo<BranchTrackingRule>,
    @InjectRepository(SourceProvider) private readonly providerRepo: TypeOrmRepo<SourceProvider>,
    private readonly clientFactory: ProviderClientFactory,
  ) {}

  async getAll(query: GetAllRepositoriesQuery): Promise<PagedResult<RepositoryDto>> {
    const { pageIndex = 1, maxResultCount = 10, searchTerm, providerId, isActive, includeDeleted } = query;
    const skip = (pageIndex - 1) * maxResultCount;

    const where: any = {};
    if (!includeDeleted) where.isDeleted = false;
    if (searchTerm) where.name = ILike(`%${searchTerm}%`);
    if (providerId) where.providerId = providerId;
    if (isActive !== undefined) where.isActive = isActive;

    const [items, totalCount] = await this.repo.findAndCount({
      where,
      skip,
      take: maxResultCount,
      order: { createdAt: 'DESC' },
    });

    return new PagedResult(totalCount, items.map(this.toDto));
  }

  async getById(id: string): Promise<GetRepositoryResponse> {
    const r = await this.repo.findOne({ where: { id, isDeleted: false } });
    if (!r) throw new NotFoundException(`Repository '${id}' not found.`);
    return this.toFullDto(r);
  }

  async create(dto: CreateRepositoryDto): Promise<GetRepositoryResponse> {
    const r = this.repo.create({
      name: dto.name,
      webUrl: dto.webUrl,
      cloneUrl: dto.cloneUrl ?? null,
      defaultBranch: dto.defaultBranch ?? 'main',
      providerId: dto.providerId,
      providerRepoId: dto.providerRepoId ?? null,
      isActive: true,
    });
    await this.repo.save(r);

    const auth = this.authRepo.create({
      repositoryId: r.id,
      authType: dto.authType,
      secretRef: dto.secretRef ?? null,
    });
    await this.authRepo.save(auth);

    const rules = (dto.branchRules ?? []).map((br) =>
      this.ruleRepo.create({ repositoryId: r.id, pattern: br.pattern, scanOnPush: br.scanOnPush ?? false }),
    );
    if (rules.length) await this.ruleRepo.save(rules);

    return this.getById(r.id);
  }

  async update(id: string, dto: UpdateRepositoryDto): Promise<GetRepositoryResponse> {
    const r = await this.repo.findOne({ where: { id, isDeleted: false } });
    if (!r) throw new NotFoundException(`Repository '${id}' not found.`);

    if (dto.name !== undefined) r.name = dto.name;
    if (dto.defaultBranch !== undefined) r.defaultBranch = dto.defaultBranch;
    if (dto.isActive !== undefined) r.isActive = dto.isActive;
    r.touchUpdated();
    await this.repo.save(r);

    if (dto.secretRef !== undefined) {
      const auth = await this.authRepo.findOne({ where: { repositoryId: id } });
      if (auth) { auth.secretRef = dto.secretRef; await this.authRepo.save(auth); }
    }

    if (dto.branchRules !== undefined) {
      await this.ruleRepo.delete({ repositoryId: id });
      const rules = dto.branchRules.map((br) =>
        this.ruleRepo.create({ repositoryId: id, pattern: br.pattern, scanOnPush: br.scanOnPush ?? false }),
      );
      if (rules.length) await this.ruleRepo.save(rules);
    }

    return this.getById(id);
  }

  async delete(id: string): Promise<void> {
    const r = await this.repo.findOne({ where: { id } });
    if (!r) throw new NotFoundException(`Repository '${id}' not found.`);
    await this.repo.remove(r);
  }

  async testConnection(dto: TestConnectionDto): Promise<TestConnectionResponse> {
    const provider = await this.providerRepo.findOne({ where: { id: dto.providerId } });
    if (!provider) return { success: false, errorMessage: 'Provider not found.' };

    try {
      const client = this.clientFactory.getClient(provider.code, provider.apiBaseUrl);
      const auth = { authType: dto.authType, token: dto.secretRef ?? '' };
      const meta = await client.getRepoMeta(dto.webUrl, auth);
      const branches = await client.getBranches(meta, auth);
      return { success: true, repoName: meta.name, providerRepoId: meta.providerRepoId, defaultBranch: meta.defaultBranch, branches };
    } catch (e) {
      return { success: false, errorMessage: (e as Error).message };
    }
  }

  private toDto(r: Repository): RepositoryDto {
    return {
      id: r.id, name: r.name, webUrl: r.webUrl, cloneUrl: r.cloneUrl,
      defaultBranch: r.defaultBranch, providerId: r.providerId,
      providerRepoId: r.providerRepoId, isActive: r.isActive,
      clonedDirectory: r.clonedDirectory, createdAt: r.createdAt,
    };
  }

  private toFullDto(r: Repository): GetRepositoryResponse {
    return {
      ...this.toDto(r),
      auth: r.auth ? { authType: r.auth.authType, secretRef: r.auth.secretRef } : null,
      branchRules: (r.branchRules ?? []).map((br) => ({ pattern: br.pattern, isEnabled: br.isEnabled, scanOnPush: br.scanOnPush })),
    };
  }
}
