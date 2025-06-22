import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, tap } from 'rxjs';
import { environment } from '../../environments/environment';

interface Candidate {
  id: number;
  nome: string;
  numero: number;
  partido: string;
}

interface VoteResponse {
  message?: string;
  erro?: string;
}

interface Resultado {
  id: number;
  nome: string;
  votos: number;
}

interface ResultadoIoT {
  id: number;
  nome: string;
  votos: number;
  media: number;
  mediana: number;
  contagem: number;
  porcentagem: number;
}

interface TipoResultado {
  titulo: string;
  resultados: Resultado[];
  total: number;
}

interface TipoResultadoIoT {
  titulo: string;
  resultados: ResultadoIoT[];
  total: number;
}

interface Results {
  eleicao1: TipoResultado;
  eleicao2: TipoResultado;
  eleicao3: TipoResultado;
  eleicao4: TipoResultado;
  eleicao5: TipoResultado;
  eleicao6: TipoResultadoIoT;
  eleicaoativa: boolean;
}

interface CreateElection {
  message: string;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;
  private endpoints = environment.endpoints;

  constructor(private http: HttpClient) {}

  // Registrar voto
  registerVote(cpf: string, candidateId: number): Observable<VoteResponse> {
    return this.http.post<VoteResponse>(`${this.apiUrl}${this.endpoints.votar}`, {
      cpf: cpf,
      candidato_id: candidateId
    });
  }

  // Obter resultados
  getResults(): Observable<Results> {
    return this.http.get<Results>(`${this.apiUrl}${this.endpoints.resultados}`);
  }

  // Listar candidatos
  getCandidates(): Observable<Candidate[]> {
    console.log('Frontend: Fazendo requisição GET para /candidatos');
    return this.http.get<Candidate[]>(`${this.apiUrl}${this.endpoints.candidatos}`).pipe(
      tap({
        next: (data) => console.log('Frontend: Dados recebidos:', data),
        error: (error) => console.error('Frontend: Erro na requisição:', error)
      })
    );
  }

  // Registrar eleitor (se necessário)
  registerVoter(cpf: string, name: string): Observable<VoteResponse> {
    return this.http.post<VoteResponse>(`${this.apiUrl}${this.endpoints.cadastrar}`, {
      cpf: cpf,
      nome: name
    });
  }

  getElectionAlternative(population: number, votes: number): Observable<CreateElection> {
    return this.http.post<CreateElection>(`${this.apiUrl}${this.endpoints.electionalternative}`, { population, votes });
  }
}
