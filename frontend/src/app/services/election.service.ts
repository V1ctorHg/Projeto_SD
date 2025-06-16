import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';


@Injectable({
  providedIn: 'root'
})
export class ElectionService {
  private readonly API_URL = 'http://localhost:5001/electionalternative';

  constructor(private http: HttpClient) {}

  private handleError(error: HttpErrorResponse) {
    console.error('Erro na requisição HTTP:', error);
    return of(null);
  }

  startElection(dados: any): Observable<any> {
    return this.http.post(this.API_URL, dados).pipe(
      tap(response => console.log('Resposta do POST:', response)),
      catchError(this.handleError.bind(this))
    );
  }
} 