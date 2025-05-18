// vote.component.ts
import { Component, OnInit, OnDestroy, ChangeDetectorRef, ViewChild, AfterViewInit, PLATFORM_ID, Inject } from '@angular/core';
import { CommonModule, isPlatformBrowser } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ElectionService, ElectionResults } from '../../services/election.service';
import { Observable, Subscription } from 'rxjs';
import { tap, distinctUntilChanged } from 'rxjs/operators';
import { Chart, ChartConfiguration, ChartData, registerables } from 'chart.js';
import { BaseChartDirective, provideCharts, withDefaultRegisterables } from 'ng2-charts';

// Configuração global do Chart.js
if (typeof window !== 'undefined') {
  Chart.register(...registerables);
}

@Component({
  selector: 'app-election-alternative',
  standalone: true,
  imports: [CommonModule, FormsModule, BaseChartDirective],
  providers: [provideCharts(withDefaultRegisterables())],
  templateUrl: './electionalternative.component.html',
  styleUrls: ['./electionalternative.component.css']
})
export class ElectionAlternativeComponent implements OnInit, OnDestroy, AfterViewInit {
  @ViewChild('doughnutCanvas') doughnutChart?: BaseChartDirective;
  @ViewChild('barCanvas') barChart?: BaseChartDirective;

  message: string = '';
  populacao_total: number = 0;
  num_cidades: number = 0;
  partidos: string = '';
  electionResults$: Observable<ElectionResults | null>;
  private subscription: Subscription = new Subscription();
  public chartsInitialized = false;
  public isBrowser: boolean;

  // Configuração do gráfico de meia lua (doughnut)
  public doughnutChartOptions: ChartConfiguration<'doughnut'>['options'] = {
    responsive: true,
    circumference: 180,
    rotation: -90,
    animation: {
      duration: 2000,
      easing: 'easeInOutCubic',
    },
    plugins: {
      legend: {
        display: true,
        position: 'bottom'
      }
    }
  };

  public doughnutChartData: ChartData<'doughnut'> = {
    labels: [],
    datasets: [{
      data: [],
      backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF'],
      label: 'Votos por Partido'
    }]
  };

  // Configuração do gráfico de barras horizontais
  public barChartOptions: ChartConfiguration<'bar'>['options'] = {
    responsive: true,
    indexAxis: 'y',
    animation: {
      duration: 2000,
      easing: 'easeInOutCubic',
    },
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      x: {
        beginAtZero: true,
        ticks: {
          callback: function(value: any) {
            return Number(value).toLocaleString();
          }
        }
      }
    }
  };

  public barChartData: ChartData<'bar'> = {
    labels: ['Total de Votos', 'Abstenção'],
    datasets: [{
      data: [0, 0],
      backgroundColor: ['#36A2EB', '#FF6384'],
      label: 'Quantidade'
    }]
  };

  constructor(
    private electionService: ElectionService,
    private cdr: ChangeDetectorRef,
    @Inject(PLATFORM_ID) platformId: Object
  ) {
    this.isBrowser = isPlatformBrowser(platformId);
    console.log('[ElectionComponent] Componente construído, isBrowser:', this.isBrowser);
    
    this.electionResults$ = this.electionService.electionResults$.pipe(
      distinctUntilChanged(),
      tap(results => {
        console.log('[ElectionComponent] Dados recebidos do observable:', results);
        if (results && this.chartsInitialized && this.isBrowser) {
          this.updateCharts(results);
        }
      })
    );
  }

  ngOnInit() {
    if (!this.isBrowser) {
      console.log('[ElectionComponent] Executando em SSR, pulando inicialização dos gráficos');
      return;
    }

    console.log('[ElectionComponent] ngOnInit - Iniciando...');
    this.subscription.add(
      this.electionResults$.subscribe({
        next: (results) => {
          console.log('[ElectionComponent] Subscription recebeu dados:', results);
          if (results) {
            console.log('[ElectionComponent] Dados válidos recebidos:', {
              serial: results.serialeleicao,
              ativa: results.ativaeleicao,
              votos: results.totalvotos,
              populacao: results.totalpopulacao,
              votos_por_partido: results.votos_por_partido
            });
          }
        },
        error: (error) => {
          console.error('[ElectionComponent] Erro na subscription:', error);
        }
      })
    );

    this.electionService.startPolling();
  }

  ngAfterViewInit() {
    if (!this.isBrowser) return;

    // Delay maior para garantir que o DOM esteja pronto
    setTimeout(() => {
      this.initializeCharts();
    }, 500);
  }

  private initializeCharts() {
    if (!this.isBrowser) return;

    try {
      this.chartsInitialized = true;
      console.log('[ElectionComponent] Gráficos inicializados');
      this.cdr.detectChanges();
    } catch (error) {
      console.error('[ElectionComponent] Erro ao inicializar gráficos:', error);
    }
  }

  private updateCharts(results: ElectionResults) {
    if (!this.isBrowser || !this.chartsInitialized) return;

    try {
      // Atualiza o gráfico de meia lua (votos por partido)
      const partidos = Object.keys(results.votos_por_partido);
      const votos = Object.values(results.votos_por_partido);
      
      this.doughnutChartData.labels = partidos;
      this.doughnutChartData.datasets[0].data = votos;

      // Atualiza o gráfico de barras (total de votos e abstenção)
      const totalVotos = results.totalvotos || 0;
      const abstencao = results.totalpopulacao - totalVotos;
      
      this.barChartData = {
        labels: ['Total de Votos', 'Abstenção'],
        datasets: [{
          data: [totalVotos, abstencao],
          backgroundColor: ['#36A2EB', '#FF6384'],
          label: 'Quantidade'
        }]
      };

      this.cdr.detectChanges();
    } catch (error) {
      console.error('Erro ao atualizar gráficos:', error);
    }
  }

  ngOnDestroy() {
    console.log('[ElectionComponent] ngOnDestroy - Limpando...');
    this.electionService.stopPolling();
    this.subscription.unsubscribe();
  }

  startElection() {
    const partidosSelecionados = this.partidos
      .split(',')
      .map(p => p.trim())
      .filter(p => p.length > 0);

    if (partidosSelecionados.length < 2) {
      this.message = 'Erro: Selecione pelo menos 2 partidos.';
      return;
    }

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
      partidos: partidosSelecionados
    };

    this.electionService.startElection(dados).subscribe({
      next: (response: any) => {
        this.message = 'Simulação iniciada com sucesso!';
      },
      error: (error) => {
        this.message = 'Erro ao iniciar a simulação: ' + error.message;
      }
    });
  }

  getVotosArray(results: ElectionResults): { nome: string; votos: number }[] {
    if (!results || !results.votos_por_partido) return [];
    return Object.entries(results.votos_por_partido).map(([nome, votos]) => ({
      nome,
      votos: Number(votos)
    }));
  }

  getAbstencao(results: ElectionResults): number {
    if (!results) return 0;
    return results.totalpopulacao - results.totalvotos;
  }

  getPartidoVencedor(results: ElectionResults): string | null {
    if (!results || results.ativaeleicao || !results.votos_por_partido) return null;
    const votos = results.votos_por_partido;
    if (Object.keys(votos).length === 0) return null;
    return Object.keys(votos).reduce((a, b) => votos[a] > votos[b] ? a : b);
  }

  getPorcentagemVencedor(results: ElectionResults): number | null {
    const vencedor = this.getPartidoVencedor(results);
    if (!vencedor || !results || results.totalvotos === 0) return null;
    return results.votos_por_partido[vencedor] / results.totalvotos;
  }

  getDefinicaoMatematica(results: ElectionResults): { definida: boolean; vencedor?: string; mensagem: string } {
    if (!results || !results.ativaeleicao) {
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

  public hasVotosPartido(results: ElectionResults): boolean {
    return results?.votos_por_partido && Object.keys(results.votos_por_partido).length > 0;
  }
}