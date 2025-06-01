// vote.component.ts
import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { Router } from '@angular/router';

interface Candidate {
  id: number;
  nome: string;
  numero: number;
  partido: string;
}

@Component({
  selector: 'app-vote',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './vote.component.html',
  styleUrls: ['./vote.component.css']
})
export class VoteComponent implements OnInit {
  candidates: Candidate[] = [];
  selectedCandidate: number | null = null;
  cpf: string = '';
  loading = false;
  error: string | null = null;
  success: string | null = null;

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.loadCandidates();
  }

  loadCandidates() {
    this.loading = true;
    this.apiService.getCandidates().subscribe({
      next: (candidates) => {
        this.candidates = candidates;
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar candidatos:', err);
        this.error = 'Erro ao carregar candidatos. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  formatCPF(cpf: string): string {
    const numbers = cpf.replace(/\D/g, '');
    
    if (numbers.length <= 3) {
      return numbers;
    } else if (numbers.length <= 6) {
      return `${numbers.slice(0, 3)}.${numbers.slice(3)}`;
    } else if (numbers.length <= 9) {
      return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6)}`;
    } else {
      return `${numbers.slice(0, 3)}.${numbers.slice(3, 6)}.${numbers.slice(6, 9)}-${numbers.slice(9, 11)}`;
    }
  }

  onCPFInput(event: Event) {
    const input = event.target as HTMLInputElement;
    let value = input.value.replace(/\D/g, '');
    
    if (value.length > 11) {
      value = value.slice(0, 11);
    }
    
    this.cpf = this.formatCPF(value);
    
    if (!value) {
      this.error = null;
      return;
    }
    
    if (value.length === 11) {
      if (!this.validateCPF(value)) {
        this.error = 'CPF inválido. Por favor, verifique o número.';
      } else {
        this.error = null;
      }
    }
  }

  validateCPF(cpf: string): boolean {

    const numbers = cpf.replace(/\D/g, '');
    
    if (numbers.length !== 11) {
      return false;
    }

    if (/^(\d)\1{10}$/.test(numbers)) {
      return false;
    }

    let sum = 0;
    let remainder;


    for (let i = 1; i <= 9; i++) {
      sum = sum + parseInt(numbers.substring(i-1, i)) * (11 - i);
    }
    remainder = (sum * 10) % 11;
    if ((remainder === 10) || (remainder === 11)) remainder = 0;
    if (remainder !== parseInt(numbers.substring(9, 10))) return false;

    sum = 0;
    for (let i = 1; i <= 10; i++) {
      sum = sum + parseInt(numbers.substring(i-1, i)) * (12 - i);
    }
    remainder = (sum * 10) % 11;
    if ((remainder === 10) || (remainder === 11)) remainder = 0;
    if (remainder !== parseInt(numbers.substring(10, 11))) return false;

    return true;
  }

  isCPFValid(): boolean {
    return Boolean(this.cpf) && this.validateCPF(this.cpf);
  }

  submitVote() {
    if (!this.selectedCandidate || !this.cpf) {
      this.error = 'Por favor, selecione um candidato e informe seu CPF.';
      return;
    }

    const cleanCPF = this.cpf.replace(/\D/g, '');
    
    if (!this.validateCPF(cleanCPF)) {
      this.error = 'CPF inválido. Por favor, verifique o número.';
      return;
    }

    this.loading = true;
    this.error = null;
    this.success = null;

    this.apiService.registerVote(cleanCPF, this.selectedCandidate).subscribe({
      next: (response) => {
        this.success = response.message || 'Voto registrado com sucesso!';
        this.loading = false;
        this.selectedCandidate = null;
        this.cpf = '';
      },
      error: (err) => {
        console.error('Erro ao registrar voto:', err);
        this.error = err.error?.erro || 'Erro ao registrar voto. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }
}