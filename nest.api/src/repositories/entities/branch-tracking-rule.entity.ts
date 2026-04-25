import { Column, Entity, Index, PrimaryGeneratedColumn } from 'typeorm';
import { AuditMixin } from '../../database/audit.mixin';

@Entity('BranchTrackingRules')
@Index(['repositoryId', 'pattern'], { unique: true })
export class BranchTrackingRule extends AuditMixin {
  @PrimaryGeneratedColumn('uuid', { name: 'Id' })
  id: string;

  @Column({ name: 'RepositoryId', type: 'uuid' })
  repositoryId: string;

  @Column({ name: 'Pattern', length: 200 })
  pattern: string;

  @Column({ name: 'IsEnabled', default: true })
  isEnabled: boolean;

  @Column({ name: 'ScanOnPush', default: false })
  scanOnPush: boolean;
}
