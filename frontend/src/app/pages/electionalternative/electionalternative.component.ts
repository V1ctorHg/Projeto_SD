// vote.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ElectionService } from '../../services/election.service';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

interface Candidate {
  id: number;
  nome: string;
  numero: number;
  partido: string;
}

@Component({
  selector: 'app-election-alternative',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './electionalternative.component.html',
  styleUrls: ['./electionalternative.component.css']
})
export class ElectionAlternativeComponent implements OnInit {
  message: string = '';
  populacao_total: number = 0;
  num_cidades: number = 0;
  candidates: Candidate[] = [];
  population: number = 0;
  votes: number = 0;
  loading = false;
  error: string | null = null;
  success: string | null = null;

  constructor(
    private electionService: ElectionService,
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadCandidates();
  }

  loadCandidates() {
    this.apiService.getCandidates().subscribe({
      next: (candidates) => {
        this.candidates = candidates;
      },
      error: (error) => {
        console.error('Erro ao carregar candidatos:', error);
      }
    });
  }

  startElection() {
    this.loading = true;
    this.error = null;
    this.success = null;

    if (this.populacao_total <= 0) {
      this.error = 'A população total deve ser maior que zero.';
      this.loading = false;
      return;
    }

    if (this.num_cidades <= 0) {
      this.error = 'O número de cidades deve ser maior que zero.';
      this.loading = false;
      return;
    }

    const dados = {
      populacao_total: this.populacao_total,
      num_cidades: this.num_cidades,
    };

    this.apiService.startElectionAlternative(dados).subscribe({
      next: (response: any) => {
        this.success = response.message || 'Simulação iniciada com sucesso! Os resultados podem levar um minuto para aparecer.';
        this.loading = false;
        setTimeout(() => {
          this.router.navigate(['/results']);
        }, 2000);
      },
      error: (err: any) => {
        console.error('Erro ao iniciar a simulação:', err);
        this.error = err.error?.message || 'Erro ao iniciar a simulação. Verifique o console para mais detalhes.';
        this.loading = false;
      }
    });
  }

  // Métodos de navegação
  goToDashboard() {
    this.router.navigate(['/dashboard']);
  }

  goToVote() {
    this.router.navigate(['/vote']);
  }

  goToResults() {
    this.router.navigate(['/results']);
  }

  logout() {
    this.apiService.logout();
    this.router.navigate(['/login']);
  }
}