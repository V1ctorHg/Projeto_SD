import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Voto {
  candidato: string;
  quantidade: number;
}

@Injectable({
  providedIn: 'root'
})
export class VotacaoService {

  private baseUrl = 'http://localhost:5000';

  constructor(private http: HttpClient) { }

  enviarVoto(voto: Voto): Observable<any> {
    return this.http.post(`${this.baseUrl}/votar`, voto);
  }

  obterResultados(): Observable<any> {
    return this.http.get(`${this.baseUrl}/resultados`);
  }
}