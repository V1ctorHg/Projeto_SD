import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

interface Candidate {
  name: string;
  number: number;
  party: string;
}

interface VoteResponse {
  message: string;
}

interface CandidateResult extends Candidate {
  votes: number;
}

interface Results {
  [key: string]: CandidateResult | boolean;
  eleicaoativa: boolean;
}

interface CreateElection {
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = 'http://localhost:5000';
  //private baseUrl = 'http://backend:5000'; //para rodar no docker

  constructor(private http: HttpClient) {}

  getCandidates(): Observable<Candidate[]> {
    return this.http.get<Candidate[]>(`${this.baseUrl}/candidates`);
  }

  vote(cpf: string, number: number): Observable<VoteResponse> {
    return this.http.post<VoteResponse>(`${this.baseUrl}/vote`, { cpf, number });
  }

  getResults(): Observable<Results> {
    return this.http.get<Results>(`${this.baseUrl}/results`);
  }

  getElectionAlternative(population: number, votes: number) {
    return this.http.post<CreateElection>(`${this.baseUrl}/electionalternative`, { population, votes });
  }
}
