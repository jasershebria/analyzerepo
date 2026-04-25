import { Body, Controller, Delete, Get, HttpCode, HttpStatus, Param, Post, Put, Query } from '@nestjs/common';
import { ApiOperation, ApiTags } from '@nestjs/swagger';
import { RepositoriesService } from './repositories.service';
import { RepoSyncService } from './repo-sync.service';
import {
  CreateRepositoryDto,
  GetAllRepositoriesQuery,
  TestConnectionDto,
  UpdateRepositoryDto,
} from './dto/repository.dto';

@ApiTags('Repositories')
@Controller('api/repositories')
export class RepositoriesController {
  constructor(
    private readonly svc: RepositoriesService,
    private readonly syncSvc: RepoSyncService,
  ) {}

  @Get()
  @ApiOperation({ summary: 'Get all repositories' })
  getAll(@Query() query: GetAllRepositoriesQuery) {
    return this.svc.getAll(query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get repository by ID' })
  getById(@Param('id') id: string) {
    return this.svc.getById(id);
  }

  @Post()
  @HttpCode(HttpStatus.CREATED)
  @ApiOperation({ summary: 'Create a new repository' })
  create(@Body() dto: CreateRepositoryDto) {
    return this.svc.create(dto);
  }

  @Put(':id')
  @ApiOperation({ summary: 'Update a repository' })
  update(@Param('id') id: string, @Body() dto: UpdateRepositoryDto) {
    return this.svc.update(id, dto);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  @ApiOperation({ summary: 'Delete a repository' })
  delete(@Param('id') id: string) {
    return this.svc.delete(id);
  }

  @Post('test-connection')
  @ApiOperation({ summary: 'Test repository connection' })
  testConnection(@Body() dto: TestConnectionDto) {
    return this.svc.testConnection(dto);
  }

  @Post(':id/sync')
  @ApiOperation({ summary: 'Clone or pull repository to local workspace' })
  sync(@Param('id') id: string) {
    return this.syncSvc.sync(id);
  }

  @Get(':id/analyze')
  @ApiOperation({ summary: 'Analyze the local workspace' })
  analyze(@Param('id') id: string) {
    return this.syncSvc.analyze(id);
  }
}
