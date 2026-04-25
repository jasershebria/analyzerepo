import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository as TypeOrmRepo } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import * as path from 'path';
import * as fs from 'fs';
import simpleGit from 'simple-git';
import { Repository } from './entities/repository.entity';
import { RepositoryAuth } from './entities/repository-auth.entity';

@Injectable()
export class RepoSyncService {
  constructor(
    @InjectRepository(Repository) private readonly repo: TypeOrmRepo<Repository>,
    @InjectRepository(RepositoryAuth) private readonly authRepo: TypeOrmRepo<RepositoryAuth>,
    private readonly config: ConfigService,
  ) {}

  async sync(repoId: string): Promise<{ status: string; workspacePath: string }> {
    const r = await this.repo.findOne({ where: { id: repoId, isDeleted: false } });
    if (!r) throw new NotFoundException(`Repository '${repoId}' not found.`);

    const auth = await this.authRepo.findOne({ where: { repositoryId: repoId } });
    const workspace = path.join(this.config.get<string>('git.cloneBasePath')!, repoId);
    const cloneUrl = this.buildAuthUrl(r.cloneUrl ?? r.webUrl, auth?.secretRef ?? null);

    if (fs.existsSync(path.join(workspace, '.git'))) {
      const git = simpleGit(workspace);
      await git.pull('origin', r.defaultBranch, ['--rebase']);
      r.clonedDirectory = workspace;
      await this.repo.save(r);
      return { status: 'pulled', workspacePath: workspace };
    }

    fs.mkdirSync(path.dirname(workspace), { recursive: true });
    await simpleGit().clone(cloneUrl, workspace);
    r.clonedDirectory = workspace;
    await this.repo.save(r);
    return { status: 'cloned', workspacePath: workspace };
  }

  async analyze(repoId: string): Promise<{ fileTree: string[]; languages: Record<string, number>; insights: string[] }> {
    const r = await this.repo.findOne({ where: { id: repoId, isDeleted: false } });
    if (!r || !r.clonedDirectory) throw new NotFoundException('Repository not synced yet.');

    const fg = await import('fast-glob');
    const files: string[] = await fg.default('**/*', {
      cwd: r.clonedDirectory,
      onlyFiles: true,
      dot: false,
      ignore: ['node_modules/**', '.git/**', 'dist/**', '__pycache__/**'],
    });

    const langCount: Record<string, number> = {};
    for (const f of files) {
      const ext = path.extname(f).toLowerCase() || 'other';
      langCount[ext] = (langCount[ext] ?? 0) + 1;
    }

    const insights: string[] = [];
    if (langCount['.ts'] || langCount['.tsx']) insights.push('TypeScript project detected');
    if (langCount['.py']) insights.push('Python project detected');
    if (langCount['.java']) insights.push('Java project detected');
    if (fs.existsSync(path.join(r.clonedDirectory, 'package.json'))) insights.push('Node.js package detected');
    if (fs.existsSync(path.join(r.clonedDirectory, 'requirements.txt'))) insights.push('Python requirements detected');

    return { fileTree: files.slice(0, 500), languages: langCount, insights };
  }

  private buildAuthUrl(url: string, token: string | null): string {
    if (!token) return url;
    try {
      const u = new URL(url);
      u.username = token;
      return u.toString();
    } catch {
      return url;
    }
  }
}
