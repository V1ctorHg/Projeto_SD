import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';

interface Resultado {
  id: number;
  nome: string;
  votos: number;
}

interface Results {
  resultados: Resultado[];
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
  resultados: Resultado[] = [];
  electionResults: Results = { resultados: [], eleicaoativa: true };
  loading = true;
  error: string | null = null;
  private pollingSubscription: any;
  private readonly POLLING_INTERVAL = 3000;  // 3 segundos

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
    this.pollingSubscription = timer(0, this.POLLING_INTERVAL).pipe(
      switchMap(() => this.apiService.getResults())
    ).subscribe({
      next: (results) => {
        this.electionResults = results;
        this.resultados = results.resultados;
        this.loading = false;
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
        this.resultados = results.resultados;
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

  sortedResults(): Resultado[] {
    return [...this.resultados].sort((a, b) => b.votos - a.votos);
  }

  calculateTotalVotes(): number {
    return this.resultados.reduce((sum, candidate) => sum + candidate.votos, 0);
  }

  calculatePercentage(votos: number): number {
    const total = this.calculateTotalVotes();
    if (total === 0) return 0;
    return Math.round((votos / total) * 100 * 100) / 100;
  }
}
