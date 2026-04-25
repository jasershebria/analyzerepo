import { ConflictException, Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { ILike, Repository } from 'typeorm';
import { SourceProvider } from './entities/source-provider.entity';
import { CreateProviderDto, GetAllProvidersQuery, ProviderDto } from './dto/provider.dto';
import { PagedResult } from '../common/dto/paged-result.dto';

@Injectable()
export class ProvidersService {
  constructor(
    @InjectRepository(SourceProvider)
    private readonly repo: Repository<SourceProvider>,
  ) {}

  async getAll(query: GetAllProvidersQuery): Promise<PagedResult<ProviderDto>> {
    const { pageIndex = 1, maxResultCount = 50, searchTerm, isActive } = query;
    const skip = (pageIndex - 1) * maxResultCount;

    const where: any = { isDeleted: false };
    if (searchTerm) where.name = ILike(`%${searchTerm}%`);
    if (isActive !== undefined) where.isActive = isActive;

    const [items, totalCount] = await this.repo.findAndCount({
      where,
      skip,
      take: maxResultCount,
      order: { createdAt: 'DESC' },
    });

    return new PagedResult(totalCount, items.map(this.toDto));
  }

  async create(dto: CreateProviderDto): Promise<ProviderDto> {
    const existing = await this.repo.findOne({ where: { code: dto.code, isDeleted: false } });
    if (existing) throw new ConflictException(`Provider with code '${dto.code}' already exists.`);

    const provider = this.repo.create({
      name: dto.name,
      code: dto.code,
      apiBaseUrl: dto.apiBaseUrl,
      isActive: true,
    });
    await this.repo.save(provider);
    return this.toDto(provider);
  }

  async delete(id: string): Promise<void> {
    const provider = await this.repo.findOne({ where: { id, isDeleted: false } });
    if (!provider) throw new NotFoundException(`Provider '${id}' not found.`);
    provider.softDelete();
    await this.repo.save(provider);
  }

  private toDto(p: SourceProvider): ProviderDto {
    return {
      id: p.id,
      name: p.name,
      code: p.code,
      apiBaseUrl: p.apiBaseUrl,
      isActive: p.isActive,
      createdAt: p.createdAt,
    };
  }
}
