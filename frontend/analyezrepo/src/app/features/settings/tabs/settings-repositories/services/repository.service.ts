import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PagedResult, RepositoryDto, CreateRepositoryCommand, CreateRepositoryResponse, TestConnectionRequest, TestConnectionResponse } from '../../../../../models/analysis.models';
import { environment } from '../../../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RepositoryService {
  private readonly http = inject(HttpClient);

  getAll(): Observable<PagedResult<RepositoryDto>> {
    return this.http.get<PagedResult<RepositoryDto>>(`${environment.apiBase}/api/repositories`);
  }

  create(command: CreateRepositoryCommand): Observable<CreateRepositoryResponse> {
    return this.http.post<CreateRepositoryResponse>(`${environment.apiBase}/api/repositories`, command);
  }

  testConnection(request: TestConnectionRequest): Observable<TestConnectionResponse> {
    return this.http.post<TestConnectionResponse>(`${environment.apiBase}/api/repositories/test-connection`, request);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${environment.apiBase}/api/repositories/${id}`);
  }
}
