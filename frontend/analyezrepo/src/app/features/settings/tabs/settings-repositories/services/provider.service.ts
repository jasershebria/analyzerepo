import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PagedResult, ProviderDto } from '../../../../../models/analysis.models';
import { environment } from '../../../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class ProviderService {
  private readonly http = inject(HttpClient);

  getAll(): Observable<PagedResult<ProviderDto>> {
    return this.http.get<PagedResult<ProviderDto>>(`${environment.apiBase}/api/providers`);
  }
}
