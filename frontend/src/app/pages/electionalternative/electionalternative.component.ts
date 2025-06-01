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
    if (this.populacao_total <= 0) {
      this.message = 'Erro: A população total deve ser maior que zero.';
      return;
    }

    if (this.num_cidades <= 0) {
      this.message = 'Erro: O número de cidades deve ser maior que zero.';
      return;
    }

    const dados = {
      populacao_total: this.populacao_total,
      num_cidades: this.num_cidades,
    };

    this.electionService.startElection(dados).subscribe({
      next: (response: any) => {
        this.message = 'Simulação iniciada com sucesso! - Veja o resultado na aba "Consultar"';
      },
      error: (error) => {
        this.message = 'Erro ao iniciar a simulação: ' + error.message;
      }
    });
  }

  submitElection() {
    if (!this.population || !this.votes) {
      this.error = 'Por favor, preencha todos os campos.';
      return;
    }

    if (this.votes > this.population) {
      this.error = 'O número de votos não pode ser maior que a população.';
      return;
    }

    this.loading = true;
    this.error = null;
    this.success = null;

    this.apiService.getElectionAlternative(this.population, this.votes).subscribe({
      next: (response) => {
        this.success = response.message;
        this.loading = false;
        // Redirecionar para resultados após 2 segundos
        setTimeout(() => {
          this.router.navigate(['/results']);
        }, 2000);
      },
      error: (err) => {
        console.error('Erro ao criar eleição alternativa:', err);
        this.error = 'Erro ao criar eleição alternativa. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }
}