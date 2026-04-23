import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  RagIndexRequest,
  RagIndexResponse,
  RagQueryRequest,
  RagQueryResponse,
  RagStatusResponse,
} from '../../../models/analysis.models';
import { environment } from '../../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class RagService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiBase}/api/rag`;

  index(request: RagIndexRequest): Observable<RagIndexResponse> {
    return this.http.post<RagIndexResponse>(`${this.base}/index`, request);
  }

  query(request: RagQueryRequest): Observable<RagQueryResponse> {
    return this.http.post<RagQueryResponse>(`${this.base}/query`, request);
  }

  status(repoId: string): Observable<RagStatusResponse> {
    return this.http.get<RagStatusResponse>(`${this.base}/status/${repoId}`);
  }

  clearIndex(repoId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/index/${repoId}`);
  }
}
