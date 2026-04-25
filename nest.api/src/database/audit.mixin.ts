import { Column, CreateDateColumn, UpdateDateColumn } from 'typeorm';

export abstract class AuditMixin {
  @CreateDateColumn({ name: 'CreatedAt', type: 'timestamptz' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'UpdatedAt', type: 'timestamptz', nullable: true })
  updatedAt: Date | null;

  @Column({ name: 'CreatedBy', length: 200, nullable: true, default: null })
  createdBy: string | null;

  @Column({ name: 'UpdatedBy', length: 200, nullable: true, default: null })
  updatedBy: string | null;

  @Column({ name: 'IsDeleted', default: false })
  isDeleted: boolean;

  @Column({ name: 'DeletedAt', type: 'timestamptz', nullable: true, default: null })
  deletedAt: Date | null;

  @Column({ name: 'DeletedBy', length: 200, nullable: true, default: null })
  deletedBy: string | null;

  softDelete(deletedBy?: string): void {
    this.isDeleted = true;
    this.deletedAt = new Date();
    this.deletedBy = deletedBy ?? null;
  }

  touchUpdated(updatedBy?: string): void {
    this.updatedAt = new Date();
    this.updatedBy = updatedBy ?? null;
  }
}
