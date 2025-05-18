import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

interface VotosPorPartido {
  [key: string]: number;
}

interface ElectionResults {
  serialeleicao: number;
  totalpopulacao: number;         // Total de eleitores aptos na simulação
  totalvotos: number;             // Votos efetivamente computados
  votos_por_partido: VotosPorPartido;
  ativaeleicao: boolean;
  totalpossiveiseleitores: number; // Universo total de eleitores (para definição matemática)
}

@Component({
  selector: 'app-election-display',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="electionResults" class="election-results-container">
      <header class="results-header">
        <h2 *ngIf="electionResults.ativaeleicao">-------- RESULTADO PARCIAL --------</h2>
        <h2 *ngIf="!electionResults.ativaeleicao">-------- RESULTADO FINAL --------</h2>
      </header>

      <section class="results-summary">
        <p><strong>Serial da Eleição:</strong> {{ electionResults.serialeleicao }}</p>
        <p><strong>Total de Votos Computados:</strong> {{ electionResults.totalvotos }}</p>
        <p><strong>Total de Eleitores (Aptos na Simulação):</strong> {{ electionResults.totalpopulacao }}</p>
      </section>

      <section class="party-votes">
        <h3>Votos por Partido:</h3>
        <ul class="party-list">
          <li *ngFor="let partido of getVotosArray()" class="party-item">
            <span class="party-name">{{ partido.nome }}:</span>
            <span class="party-vote-count">{{ partido.votos }}</span>
            <span class="party-percentage" *ngIf="electionResults.totalvotos > 0">
              ({{ (partido.votos / electionResults.totalvotos) | percent:'1.2-2' }})
            </span>
          </li>
        </ul>
      </section>

      <section *ngIf="electionResults.ativaeleicao" class="partial-info">
        <hr>
        <p class="status-message"><strong>Status:</strong> {{ definicaoMatematica.mensagem }}</p>
      </section>

      <section class="abstention-info">
        <hr>
        <p><strong>Abstenção:</strong> {{ abstencao }}</p>
        <p *ngIf="taxaAbstencao !== null">
          <strong>Taxa de Abstenção:</strong> {{ taxaAbstencao | percent:'1.2-2' }}
        </p>
      </section>

      <section *ngIf="!electionResults.ativaeleicao" class="final-info">
        <hr>
        <h3 class="winner-title">Resultado Consolidado:</h3>
        <p *ngIf="partidoVencedorFinal" class="winner-details">
          <strong>Partido Vencedor:</strong> <span class="winner-name">{{ partidoVencedorFinal }}</span>
        </p>
        <p *ngIf="porcentagemVencedorFinal !== null && partidoVencedorFinal" class="winner-percentage">
          <strong>Porcentagem do Vencedor:</strong> {{ porcentagemVencedorFinal | percent:'1.2-2' }}
        </p>
        <p *ngIf="!partidoVencedorFinal && electionResults.totalvotos > 0" class="tie-message">
          Não foi possível determinar um vencedor único ou ocorreu empate.
        </p>
        <p *ngIf="electionResults.totalvotos === 0" class="no-votes-message">
          Nenhum voto foi computado nesta eleição.
        </p>
      </section>

      <footer class="results-footer" *ngIf="!electionResults.ativaeleicao">
        --------------------------------
      </footer>
    </div>

    <div *ngIf="!electionResults" class="loading-results">
      <p>Aguardando resultados da simulação...</p>
    </div>
  `,
  styles: [`
    .election-results-container {
      padding: 20px;
      border: 1px solid #ddd;
      border-radius: 8px;
      margin-top: 20px;
    }
    .results-header {
      text-align: center;
      margin-bottom: 20px;
    }
    .party-list {
      list-style: none;
      padding: 0;
    }
    .party-item {
      margin: 10px 0;
      padding: 10px;
      background: #f5f5f5;
      border-radius: 4px;
    }
    .party-name {
      font-weight: bold;
      margin-right: 10px;
    }
    .winner-name {
      color: #2196f3;
      font-weight: bold;
    }
    .loading-results {
      text-align: center;
      padding: 20px;
      color: #666;
    }
    hr {
      margin: 20px 0;
      border: 0;
      border-top: 1px solid #ddd;
    }
  `]
})
export class ElectionDisplayComponent {
  @Input() electionResults: ElectionResults | null = null;

  get abstencao(): number | null {
    if (!this.electionResults) return null;
    return this.electionResults.totalpopulacao - this.electionResults.totalvotos;
  }

  get taxaAbstencao(): number | null {
    if (!this.electionResults || this.abstencao === null || this.electionResults.totalpopulacao === 0) return null;
    return this.abstencao / this.electionResults.totalpopulacao;
  }

  get partidoVencedorFinal(): string | null {
    if (!this.electionResults || this.electionResults.ativaeleicao) return null;
    const votos = this.electionResults.votos_por_partido;
    if (!votos || Object.keys(votos).length === 0) return null;
    return Object.keys(votos).reduce((a, b) => votos[a] > votos[b] ? a : b);
  }

  get porcentagemVencedorFinal(): number | null {
    if (!this.partidoVencedorFinal || !this.electionResults || this.electionResults.totalvotos === 0) return null;
    return this.electionResults.votos_por_partido[this.partidoVencedorFinal] / this.electionResults.totalvotos;
  }

  get definicaoMatematica(): { definida: boolean; vencedor?: string; mensagem: string } {
    if (!this.electionResults || !this.electionResults.ativaeleicao) {
      return { definida: false, mensagem: '' };
    }

    const votosPartido = this.electionResults.votos_por_partido;
    const totalVotosComputados = this.electionResults.totalvotos;
    const votosAindaNoUniverso = this.electionResults.totalpossiveiseleitores - totalVotosComputados;

    if (votosAindaNoUniverso < 0) {
      const nomes = Object.keys(votosPartido);
      if (nomes.length === 0) return { definida: true, mensagem: "Eleição definida (sem votos/partidos)." };
      const vencedorAtual = nomes.reduce((a,b) => votosPartido[a] > votosPartido[b] ? a : b);
      return { definida: true, vencedor: vencedorAtual, mensagem: `Eleição matematicamente definida! (Votos do universo apurados) - ${vencedorAtual}` };
    }
    
    const nomesPartidos = Object.keys(votosPartido);
    if (nomesPartidos.length === 0) {
      return { definida: false, mensagem: "Nenhum partido com votos para análise." };
    }
    if (nomesPartidos.length === 1) {
      return { definida: true, vencedor: nomesPartidos[0], mensagem: `Eleição matematicamente definida! - ${nomesPartidos[0]}` };
    }

    const partidosOrdenados = nomesPartidos.sort((a, b) => votosPartido[b] - votosPartido[a]);
    const lider = partidosOrdenados[0];
    const segundoLugar = partidosOrdenados[1];
    const votosLider = votosPartido[lider];
    const votosSegundo = votosPartido[segundoLugar];
    const diferencaVotos = votosLider - votosSegundo;

    if (diferencaVotos > votosAindaNoUniverso) {
      return { definida: true, vencedor: lider, mensagem: `Eleição matematicamente definida! - ${lider}` };
    } else {
      return { definida: false, mensagem: "Eleição não matematicamente definida." };
    }
  }

  getVotosArray(): { nome: string; votos: number }[] {
    if (!this.electionResults || !this.electionResults.votos_por_partido) return [];
    return Object.entries(this.electionResults.votos_por_partido).map(([nome, votos]) => ({
      nome,
      votos: Number(votos)
    }));
  }
} 