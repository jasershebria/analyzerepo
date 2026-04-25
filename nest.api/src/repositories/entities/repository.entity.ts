import { Column, Entity, JoinColumn, OneToMany, OneToOne, PrimaryGeneratedColumn } from 'typeorm';
import { AuditMixin } from '../../database/audit.mixin';
import { RepositoryAuth } from './repository-auth.entity';
import { BranchTrackingRule } from './branch-tracking-rule.entity';

@Entity('Repositories')
export class Repository extends AuditMixin {
  @PrimaryGeneratedColumn('uuid', { name: 'Id' })
  id: string;

  @Column({ name: 'Name', length: 200 })
  name: string;

  @Column({ name: 'WebUrl', length: 500 })
  webUrl: string;

  @Column({ name: 'CloneUrl', length: 500, nullable: true, default: null })
  cloneUrl: string | null;

  @Column({ name: 'DefaultBranch', length: 100, default: 'main' })
  defaultBranch: string;

  @Column({ name: 'ProviderId', type: 'uuid' })
  providerId: string;

  @Column({ name: 'ProviderRepoId', length: 100, nullable: true, default: null })
  providerRepoId: string | null;

  @Column({ name: 'ProviderWorkspaceId', length: 100, nullable: true, default: null })
  providerWorkspaceId: string | null;

  @Column({ name: 'LastSeenAtUtc', type: 'timestamptz', nullable: true, default: null })
  lastSeenAtUtc: Date | null;

  @Column({ name: 'IsActive', default: true })
  isActive: boolean;

  @Column({ name: 'ClonedDirectory', length: 500, nullable: true, default: null })
  clonedDirectory: string | null;

  @OneToOne(() => RepositoryAuth, { cascade: true, eager: true, nullable: true })
  @JoinColumn({ name: 'Id', referencedColumnName: 'repositoryId' })
  auth: RepositoryAuth | null;

  @OneToMany(() => BranchTrackingRule, (rule) => rule.repositoryId, { cascade: true, eager: true })
  branchRules: BranchTrackingRule[];
}
