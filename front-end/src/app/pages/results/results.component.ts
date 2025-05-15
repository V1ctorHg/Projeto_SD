import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ApiService } from '../../services/api.service';

interface Candidate {
  name: string;
  number: number;
  party: string;
}

interface CandidateResult extends Candidate {
  votes: number;
}

interface Results {
  [key: string]: CandidateResult;
}

@Component({
  selector: 'app-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './results.component.html',
  styleUrls: ['./results.component.css']
})
export class ResultsComponent implements OnInit {
  results: Results = {};
  loading = true;
  error: string | null = null;

  protected readonly Object = Object;

  constructor(private apiService: ApiService) {}

  ngOnInit() {
    this.loadResults();
  }

  private loadResults() {
    this.loading = true;
    this.error = null;
    
    this.apiService.getResults().subscribe({
      next: (data) => {
        // console.log('Dados recebidos:', data);
        if (!data || typeof data !== 'object') {
          this.error = 'Formato de dados inválido';
          return;
        }
        this.results = data;
        //console.log('Resultados processados:', this.results);
        //console.log('Resultados ordenados:', this.sortedResults());
        this.loading = false;
      },
      error: (err) => {
        console.error('Erro ao carregar resultados:', err);
        this.error = 'Erro ao carregar resultados. Por favor, tente novamente.';
        this.loading = false;
      }
    });
  }

  sortedResults(): CandidateResult[] {
    if (!this.results) return [];
    const results = Object.values(this.results)
      .filter(r => r && typeof r === 'object' && 'votes' in r)
      .sort((a, b) => b.votes - a.votes);
    return results;
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
