import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PagedResult, ProviderDto, CreateProviderCommand } from '../../../../../models/analysis.models';
import { environment } from '../../../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ProviderService {
  private readonly http = inject(HttpClient);

  getAll(): Observable<PagedResult<ProviderDto>> {
    return this.http.get<PagedResult<ProviderDto>>(`${environment.apiBase}/api/providers`);
  }

  create(command: CreateProviderCommand): Observable<ProviderDto> {
    return this.http.post<ProviderDto>(`${environment.apiBase}/api/providers`, command);
  }

  delete(id: string): Observable<void> {
    return this.http.delete<void>(`${environment.apiBase}/api/providers/${id}`);
  }
}
