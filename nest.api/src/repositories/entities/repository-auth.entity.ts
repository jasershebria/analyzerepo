import { Column, Entity, JoinColumn, ManyToOne, PrimaryGeneratedColumn } from 'typeorm';
import { AuditMixin } from '../../database/audit.mixin';

export enum AuthType {
  PersonalAccessToken = 1,
  OAuth = 2,
  AppInstallation = 3,
}

@Entity('RepositoryAuths')
export class RepositoryAuth extends AuditMixin {
  @PrimaryGeneratedColumn('uuid', { name: 'Id' })
  id: string;

  @Column({ name: 'RepositoryId', type: 'uuid' })
  repositoryId: string;

  @Column({ name: 'AuthType', type: 'int' })
  authType: AuthType;

  @Column({ name: 'SecretRef', length: 500, nullable: true, default: null })
  secretRef: string | null;

  @Column({ name: 'ExpiresAt', type: 'timestamptz', nullable: true, default: null })
  expiresAt: Date | null;
}
