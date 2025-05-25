import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ElectionService, ElectionResults } from '../../services/election.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-election-display',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div *ngIf="electionResults$ | async as results" class="election-results-container">
      <header class="results-header">
        <h2>{{ results.ativaeleicao ? '-------- RESULTADO PARCIAL --------' : '-------- RESULTADO FINAL --------' }}</h2>
      </header>

      <section class="results-summary">
        <p><strong>Serial da Eleição:</strong> {{ results.serialeleicao | number:'1.0-0' }}</p>
        <p><strong>Total de Votos Computados:</strong> {{ results.totalvotos | number }}</p>
        <p><strong>Total de Eleitores (Aptos na Simulação):</strong> {{ results.totalpopulacao | number }}</p>
      </section>

      <section class="party-votes">
        <h3>Votos por Partido:</h3>
        <ul class="party-list">
          <li *ngFor="let partido of getVotosArray(results)" class="party-item">
            <span class="party-name">{{ partido.nome }}:</span>
            <span class="party-vote-count">{{ partido.votos | number }}</span>
            <span class="party-percentage" *ngIf="results.totalvotos > 0">
              ({{ (partido.votos / results.totalvotos) | percent:'1.2-2' }})
            </span>
          </li>
        </ul>
      </section>

      <section *ngIf="results.ativaeleicao" class="partial-info">
        <hr>
        <p class="status-message"><strong>Status:</strong> {{ getDefinicaoMatematica(results).mensagem }}</p>
      </section>

      <section class="abstention-info">
        <hr>
        <p><strong>Abstenção:</strong> {{ getAbstencao(results) | number }}</p>
        <p><strong>Taxa de Abstenção:</strong> 
          {{ getAbstencao(results) / results.totalpopulacao | percent:'1.2-2' }}
        </p>
      </section>

      <section *ngIf="!results.ativaeleicao" class="final-info">
        <hr>
        <h3 class="winner-title">Resultado Consolidado:</h3>
        <p *ngIf="getPartidoVencedor(results)" class="winner-details">
          <strong>Partido Vencedor:</strong> 
          <span class="winner-name">{{ getPartidoVencedor(results) }}</span>
        </p>
        <p *ngIf="getPartidoVencedor(results)" class="winner-percentage">
          <strong>Porcentagem do Vencedor:</strong> 
          {{ getPorcentagemVencedor(results) | percent:'1.2-2' }}
        </p>
        <p *ngIf="!getPartidoVencedor(results) && results.totalvotos > 0" class="tie-message">
          Não foi possível determinar um vencedor único ou ocorreu empate.
        </p>
        <p *ngIf="results.totalvotos === 0" class="no-votes-message">
          Nenhum voto foi computado nesta eleição.
        </p>
      </section>

      <footer class="results-footer" *ngIf="!results.ativaeleicao">
        --------------------------------
      </footer>

      {{ debugLog(results) }}
    </div>

    <div *ngIf="!(electionResults$ | async)" class="loading-results">
      <p>Aguardando resultados da simulação...</p>
    </div>
  `,
  styles: [`
    .election-results-container {
      margin-top: 20px;
      padding: 20px;
      border: 1px solid #ddd;
      border-radius: 8px;
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
export class ElectionDisplayComponent implements OnInit, OnDestroy {
  readonly electionResults$;
  private subscription: Subscription;

  constructor(private electionService: ElectionService) {
    console.log('ElectionDisplayComponent construído');
    this.electionResults$ = this.electionService.electionResults$;
    
    // Adiciona uma subscrição direta para debug
    this.subscription = this.electionResults$.subscribe(
      results => console.log('ElectionDisplayComponent recebeu dados:', results)
    );
  }

  ngOnInit() {
    console.log('ElectionDisplayComponent iniciado');
  }

  ngOnDestroy() {
    console.log('ElectionDisplayComponent destruído');
    if (this.subscription) {
      this.subscription.unsubscribe();
    }
  }

  // Função para debug no template
  debugLog(results: ElectionResults | null): string {
    console.log('Template renderizando com dados:', results);
    return '';
  }

  getVotosArray(results: ElectionResults): { nome: string; votos: number }[] {
    return Object.entries(results.votos_por_partido).map(([nome, votos]) => ({
      nome,
      votos: Number(votos)
    }));
  }

  getAbstencao(results: ElectionResults): number {
    return results.totalpopulacao - results.totalvotos;
  }

  getPartidoVencedor(results: ElectionResults): string | null {
    if (results.ativaeleicao || !results.votos_por_partido) return null;
    const votos = results.votos_por_partido;
    if (Object.keys(votos).length === 0) return null;
    return Object.keys(votos).reduce((a, b) => votos[a] > votos[b] ? a : b);
  }

  getPorcentagemVencedor(results: ElectionResults): number | null {
    const vencedor = this.getPartidoVencedor(results);
    if (!vencedor || results.totalvotos === 0) return null;
    return results.votos_por_partido[vencedor] / results.totalvotos;
  }

  getDefinicaoMatematica(results: ElectionResults): { definida: boolean; vencedor?: string; mensagem: string } {
    if (!results.ativaeleicao) {
      return { definida: false, mensagem: '' };
    }

    const votosPartido = results.votos_por_partido;
    const totalVotosComputados = results.totalvotos;
    const votosAindaNoUniverso = results.totalpossiveiseleitores - totalVotosComputados;

    if (votosAindaNoUniverso < 0) {
      const nomes = Object.keys(votosPartido);
      if (nomes.length === 0) return { definida: true, mensagem: "Eleição definida (sem votos/partidos)." };
      const vencedorAtual = nomes.reduce((a,b) => votosPartido[a] > votosPartido[b] ? a : b);
      return { 
        definida: true, 
        vencedor: vencedorAtual, 
        mensagem: `Eleição matematicamente definida! (Votos do universo apurados) - ${vencedorAtual}` 
      };
    }
    
    const nomesPartidos = Object.keys(votosPartido);
    if (nomesPartidos.length === 0) {
      return { definida: false, mensagem: "Nenhum partido com votos para análise." };
    }
    if (nomesPartidos.length === 1) {
      return { 
        definida: true, 
        vencedor: nomesPartidos[0], 
        mensagem: `Eleição matematicamente definida! - ${nomesPartidos[0]}` 
      };
    }

    const partidosOrdenados = nomesPartidos.sort((a, b) => votosPartido[b] - votosPartido[a]);
    const lider = partidosOrdenados[0];
    const segundoLugar = partidosOrdenados[1];
    const votosLider = votosPartido[lider];
    const votosSegundo = votosPartido[segundoLugar];
    const diferencaVotos = votosLider - votosSegundo;

    if (diferencaVotos > votosAindaNoUniverso) {
      return { 
        definida: true, 
        vencedor: lider, 
        mensagem: `Eleição matematicamente definida! - ${lider}` 
      };
    } else {
      return { definida: false, mensagem: "Eleição não matematicamente definida." };
    }
  }
} 