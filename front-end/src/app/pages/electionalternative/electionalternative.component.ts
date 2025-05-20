// vote.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ElectionService } from '../../services/election.service';
import { ApiService } from '../../services/api.service';

interface Candidate {
  name: string;
  number: number;
  party: string;
}

@Component({
  selector: 'app-election-alternative',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="container">
      <h2>Iniciar Nova Eleição</h2>
      
      <div class="candidates-section">
        <h3>Candidatos Participantes:</h3>
        <div class="candidates-list">
          <div *ngFor="let candidate of candidates" class="candidate-item">
            {{ candidate.name }} - Número: {{ candidate.number }} - Partido: {{ candidate.party }}
          </div>
        </div>
      </div>

      <div class="form-group">
        <label for="populacao">População Total:</label>
        <input type="number" id="populacao" [(ngModel)]="populacao_total" class="form-control">
      </div>

      <div class="form-group">
        <label for="cidades">Número de Cidades:</label>
        <input type="number" id="cidades" [(ngModel)]="num_cidades" class="form-control">
      </div>

      <button (click)="startElection()" class="btn-submit">Iniciar Eleição</button>

      <div *ngIf="message" class="message">
        {{ message }}
      </div>
    </div>
  `,
  styles: [`
    .container {
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }

    h2, h3 {
      text-align: center;
      color: #333;
      margin-bottom: 20px;
    }

    .candidates-section {
      margin-bottom: 30px;
      padding: 15px;
      background: #f5f5f5;
      border-radius: 8px;
    }

    .candidates-list {
      margin-top: 15px;
    }

    .candidate-item {
      padding: 10px;
      border-bottom: 1px solid #ddd;
      color: #444;
    }

    .candidate-item:last-child {
      border-bottom: none;
    }

    .form-group {
      margin-bottom: 20px;
    }

    label {
      display: block;
      margin-bottom: 5px;
      color: #666;
    }

    .form-control {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 16px;
    }

    .btn-submit {
      width: 100%;
      padding: 10px;
      background: #2196f3;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 16px;
      margin-top: 20px;
    }

    .btn-submit:hover {
      background: #1976d2;
    }

    .message {
      margin-top: 20px;
      padding: 10px;
      border-radius: 4px;
      text-align: center;
      background: #e8f5e9;
      color: #2e7d32;
    }
  `]
})
export class ElectionAlternativeComponent implements OnInit {
  message: string = '';
  populacao_total: number = 0;
  num_cidades: number = 0;
  candidates: Candidate[] = [];

  constructor(
    private electionService: ElectionService,
    private apiService: ApiService
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
}