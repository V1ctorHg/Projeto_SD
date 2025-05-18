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
  [key: string]: CandidateResult;
}

interface CreateElection {
  message: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  createElection(population: number, votes: number) {
    throw new Error('Method not implemented.');
  }
  private baseUrl = 'http://localhost:5000'; // Porta do app.py

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




/*
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://127.0.0.1:5000';

  constructor(private http: HttpClient) {}

  getCandidates(): Observable<any> {
    return this.http.get(`${this.baseUrl}/candidates`);
  }

  vote(cpf: string, number: number): Observable<any> {
    return this.http.post(`${this.baseUrl}/vote`, { cpf, number });
  }

  getResults(): Observable<any> {
    return this.http.get(`${this.baseUrl}/results`);
  }
}
  */
