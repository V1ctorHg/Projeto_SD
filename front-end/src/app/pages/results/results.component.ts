import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';

interface Candidate {
  name: string;
  number: number;
  party: string;
}

interface CandidateResult extends Candidate {
  votes: number;
}

interface ElectionResults {
  [key: string]: CandidateResult | boolean;
  eleicaoativa: boolean;
}

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent implements OnInit, OnDestroy {
  electionResults: ElectionResults = {
    eleicaoativa: false
  };
  loading = true;
  error: string | null = null;
  private pollingSubscription: any;
  private readonly POLLING_INTERVAL_ACTIVE = 3000;  // 3 segundos quando ativa
  private readonly POLLING_INTERVAL_INACTIVE = 10000;  // 30 segundos quando inativa

  protected readonly Object = Object;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.startPolling();
  }

  ngOnDestroy() {
    this.stopPolling();
  }

  private startPolling() {
    // Primeira requisição imediata
    this.fetchResults();

    // Inicia o polling
    this.pollingSubscription = timer(0, this.POLLING_INTERVAL_ACTIVE).pipe(
      switchMap(() => this.apiService.getResults())
    ).subscribe({
      next: (results) => {
        this.electionResults = results;
        this.loading = false;

        // Se a eleição não está mais ativa, muda o intervalo
        if (!results.eleicaoativa) {
          this.restartPollingWithLowerFrequency();
        }
      },
      error: (err) => {
        console.error('Erro ao carregar resultados:', err);
        this.error = 'Erro ao carregar resultados. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  private fetchResults() {
    this.apiService.getResults().subscribe({
      next: (results) => {
        this.electionResults = results;
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar resultados:', err);
        this.error = 'Erro ao carregar resultados. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  private restartPollingWithLowerFrequency() {
    this.stopPolling();
    
    this.pollingSubscription = timer(0, this.POLLING_INTERVAL_INACTIVE).pipe(
      switchMap(() => this.apiService.getResults())
    ).subscribe({
      next: (results) => {
        this.electionResults = results;
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar resultados:', err);
        this.error = 'Erro ao carregar resultados. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  private stopPolling() {
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  sortedResults(): CandidateResult[] {
    return Object.entries(this.electionResults)
      .filter(([key, value]) => 
        key !== 'eleicaoativa' && typeof value === 'object' && 'votes' in value)
      .map(([_, value]) => value as CandidateResult)
      .sort((a, b) => b.votes - a.votes);
  }

  calculateTotalVotes(): number {
    return this.sortedResults()
      .reduce((sum, candidate) => sum + candidate.votes, 0);
  }

  calculatePercentage(votes: number): number {
    const total = this.calculateTotalVotes();
    if (total === 0) return 0;
    return Math.round((votes / total) * 100 * 100) / 100;
  }
}
