// vote.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';

interface Candidate {
  name: string;
  number: number;
  party: string;
}

@Component({
  selector: 'app-vote',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="vote-container">
      <h2>Votação</h2>
      
      <div *ngIf="loading" class="loading">
        Carregando candidatos...
      </div>

      <div *ngIf="!loading">
        <div class="form-group">
          <label for="cpf">CPF:</label>
          <input type="text" 
                 id="cpf" 
                 [(ngModel)]="cpf" 
                 (input)="formatCPF($event)"
                 placeholder="Digite seu CPF"
                 maxlength="14">
          <div *ngIf="cpfError" class="error-message">
            {{ cpfError }}
          </div>
        </div>

        <div class="candidates-list">
          <h3>Candidatos Disponíveis:</h3>
          <div *ngIf="candidates.length === 0" class="no-candidates">
            Nenhum candidato disponível no momento.
          </div>
          <div *ngFor="let candidate of candidates" class="candidate-item">
            <button (click)="selectedNumber = candidate.number" 
                    [class.selected]="selectedNumber === candidate.number">
              {{ candidate.name }} - Número: {{ candidate.number }}
            </button>
          </div>
        </div>

        <button (click)="submitVote()" 
                class="submit-button" 
                [disabled]="!isValidCPF() || !selectedNumber">
          Confirmar Voto
        </button>

        <div *ngIf="message" [class]="message.includes('sucesso') ? 'success' : 'error'">
          {{ message }}
        </div>
      </div>
    </div>
  `,
  styles: [`
    .vote-container {
      max-width: 600px;
      margin: 0 auto;
      padding: 20px;
    }
    .loading {
      text-align: center;
      padding: 20px;
      font-style: italic;
      color: #666;
    }
    .no-candidates {
      text-align: center;
      padding: 20px;
      color: #666;
      border: 1px dashed #ddd;
      border-radius: 4px;
    }
    .form-group {
      margin-bottom: 20px;
    }
    .form-group label {
      display: block;
      margin-bottom: 5px;
    }
    .form-group input {
      width: 100%;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 16px;
    }
    .error-message {
      color: #d32f2f;
      font-size: 0.9em;
      margin-top: 5px;
    }
    .candidates-list {
      margin: 20px 0;
    }
    .candidate-item {
      margin: 10px 0;
    }
    .candidate-item button {
      width: 100%;
      padding: 10px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
      cursor: pointer;
      transition: all 0.3s ease;
    }
    .candidate-item button:hover {
      background: #f5f5f5;
    }
    .candidate-item button.selected {
      background: #e3f2fd;
      border-color: #2196f3;
    }
    .submit-button {
      width: 100%;
      padding: 10px;
      background: #2196f3;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      transition: background-color 0.3s;
    }
    .submit-button:disabled {
      background: #ccc;
      cursor: not-allowed;
    }
    .submit-button:not(:disabled):hover {
      background: #1976d2;
    }
    .success {
      color: green;
      margin-top: 10px;
      padding: 10px;
      background: #e8f5e9;
      border-radius: 4px;
      text-align: center;
    }
    .error {
      color: #d32f2f;
      margin-top: 10px;
      padding: 10px;
      background: #ffebee;
      border-radius: 4px;
      text-align: center;
    }
  `]
})
export class VoteComponent implements OnInit {
  candidates: Candidate[] = [];
  cpf = '';
  cpfError: string | null = null;
  selectedNumber: number | null = null;
  message = '';
  loading = true;

  constructor(private api: ApiService) {}

  ngOnInit() {
    this.loadCandidates();
  }

  private loadCandidates() {
    this.loading = true;
    this.api.getCandidates().subscribe({
      next: (data) => {
        this.candidates = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Erro ao carregar candidatos:', error);
        this.message = 'Erro ao carregar candidatos. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  formatCPF(event: any) {
    let value = event.target.value.replace(/\D/g, '');
    if (value.length <= 11) {
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d)/, '$1.$2');
      value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
      this.cpf = value;
      this.validateCPF();
    }
  }

  validateCPF() {
    const cpf = this.cpf.replace(/\D/g, '');
    
    if (cpf.length === 0) {
      this.cpfError = null;
      return;
    }
    
    if (cpf.length !== 11) {
      this.cpfError = 'CPF deve ter 11 dígitos';
      return;
    }

    if (/^(\d)\1{10}$/.test(cpf)) {
      this.cpfError = 'CPF inválido';
      return;
    }

    let sum = 0;
    let remainder;

    for (let i = 1; i <= 9; i++) {
      sum = sum + parseInt(cpf.substring(i - 1, i)) * (11 - i);
    }

    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.substring(9, 10))) {
      this.cpfError = 'CPF inválido';
      return;
    }

    sum = 0;
    for (let i = 1; i <= 10; i++) {
      sum = sum + parseInt(cpf.substring(i - 1, i)) * (12 - i);
    }

    remainder = (sum * 10) % 11;
    if (remainder === 10 || remainder === 11) remainder = 0;
    if (remainder !== parseInt(cpf.substring(10, 11))) {
      this.cpfError = 'CPF inválido';
      return;
    }

    this.cpfError = null;
  }

  isValidCPF(): boolean {
    return this.cpf.replace(/\D/g, '').length === 11 && !this.cpfError;
  }

  submitVote() {
    if (!this.isValidCPF() || !this.selectedNumber) {
      this.message = 'Por favor, preencha todos os campos corretamente.';
      return;
    }

    const cpf = this.cpf.replace(/\D/g, '');
    this.message = '';
    this.api.vote(cpf, this.selectedNumber).subscribe({
      next: (res) => {
        this.message = 'Voto registrado com sucesso!';
        this.cpf = '';
        this.selectedNumber = null;
      },
      error: (err) => {
        if (err.error?.error === 'CPF já votou!') {
          this.message = 'Este CPF já votou nesta eleição.';
        } else {
          this.message = err.error?.error || 'Erro ao votar. Por favor, tente novamente.';
        }
      }
    });
  }
}