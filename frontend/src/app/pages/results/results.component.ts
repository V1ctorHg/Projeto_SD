import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';
import { timer } from 'rxjs';
import { switchMap } from 'rxjs/operators';

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

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent implements OnInit, OnDestroy {
  electionResults: Results = {
    eleicao1: { titulo: "Eleição Atual", resultados: [], total: 0 },
    eleicao2: { titulo: "Eleição Grupo 2", resultados: [], total: 0 },
    eleicao3: { titulo: "Melhor Pokemon", resultados: [], total: 0 },
    eleicao4: { titulo: "Melhor Ator", resultados: [], total: 0 },
    eleicao5: { titulo: "Melhor Filme 2025", resultados: [], total: 0 },
    eleicao6: { titulo: "IoT - Dados Estatísticos", resultados: [], total: 0 },
    eleicaoativa: true
  };
  loading = true;
  error: string | null = null;
  private pollingSubscription: any;
  private readonly POLLING_INTERVAL = 3000;  // 3 segundos

  protected readonly Object = Object;

  constructor(private apiService: ApiService, private router: Router) {}

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

  sortedResults(resultados: Resultado[]): Resultado[] {
    return [...resultados].sort((a, b) => b.votos - a.votos);
  }

  sortedResultsIoT(resultados: ResultadoIoT[]): ResultadoIoT[] {
    return [...resultados].sort((a, b) => b.votos - a.votos);
  }

  calculatePercentage(votos: number, total: number): number {
    if (total === 0) return 0;
    return Math.round((votos / total) * 100 * 100) / 100;
  }

  getEleicoes(): { key: string, data: TipoResultado }[] {
    return [
      { key: 'eleicao1', data: this.electionResults.eleicao1 },
      { key: 'eleicao2', data: this.electionResults.eleicao2 },
      { key: 'eleicao3', data: this.electionResults.eleicao3 },
      { key: 'eleicao4', data: this.electionResults.eleicao4 },
      { key: 'eleicao5', data: this.electionResults.eleicao5 }
    ];
  }

  getEleicaoIoT(): TipoResultadoIoT {
    return this.electionResults.eleicao6;
  }

  getTotalGeral(): number {
    return this.electionResults.eleicao1.total + 
           this.electionResults.eleicao2.total + 
           this.electionResults.eleicao3.total +
           this.electionResults.eleicao4.total +
           this.electionResults.eleicao5.total +
           this.electionResults.eleicao6.total;
  }

  retryLoad() {
    this.fetchResults();
  }

  // Métodos de navegação
  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  goToVote() {
    this.router.navigate(['/vote']);
  }

  goToElectionAlternative() {
    this.router.navigate(['/electionalternative']);
  }

  logout() {
    this.apiService.logout();
    this.router.navigate(['/login']);
  }
}
