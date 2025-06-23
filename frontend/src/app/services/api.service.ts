import { HttpClient, HttpHeaders } from '@angular/common/http';
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

interface LoginResponse {
  message: string;
  access_token: string;
  username: string;
}

interface LoginRequest {
  username: string;
  password: string;
}

interface TokenVerification {
  valid: boolean;
  username: string;
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

  // Método para obter headers com token de autenticação
  private getAuthHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    });
  }

  // Login
  login(username: string, password: string): Observable<LoginResponse> {
    return this.http.post<LoginResponse>(`${this.apiUrl}/login`, {
      username,
      password
    });
  }

  // Verificar token
  verifyToken(): Observable<TokenVerification> {
    return this.http.get<TokenVerification>(`${this.apiUrl}/verify-token`, {
      headers: this.getAuthHeaders()
    });
  }

  // Logout
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
  }

  // Verificar se está autenticado
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  // Registrar voto
  registerVote(cpf: string, candidateId: number): Observable<VoteResponse> {
    return this.http.post<VoteResponse>(`${this.apiUrl}${this.endpoints.votar}`, {
      cpf: cpf,
      candidato_id: candidateId
    }, { headers: this.getAuthHeaders() });
  }

  // Obter resultados
  getResults(): Observable<Results> {
    return this.http.get<Results>(`${this.apiUrl}${this.endpoints.resultados}`, {
      headers: this.getAuthHeaders()
    });
  }

  // Listar candidatos
  getCandidates(): Observable<Candidate[]> {
    console.log('Frontend: Fazendo requisição GET para /candidatos');
    return this.http.get<Candidate[]>(`${this.apiUrl}${this.endpoints.candidatos}`, {
      headers: this.getAuthHeaders()
    }).pipe(
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
    }, { headers: this.getAuthHeaders() });
  }

  startElectionAlternative(data: { populacao_total: number, num_cidades: number }): Observable<CreateElection> {
    return this.http.post<CreateElection>(`${this.apiUrl}/electionalternative`,
      data,
      { headers: this.getAuthHeaders() }
    );
  }
}
