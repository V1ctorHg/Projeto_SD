import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { BehaviorSubject, Observable, timer, Observer, of } from 'rxjs';
import { switchMap, catchError, retry, tap, map } from 'rxjs/operators';

//depois colocar aqui o usuário que solicitou a eleição e o timestamp

export interface ElectionResults {
  serialeleicao: number;
  totalpopulacao: number;
  totalvotos: number;
  votos_por_partido: { [key: string]: number };
  ativaeleicao: boolean;
  totalpossiveiseleitores: number;
}

@Injectable({
  providedIn: 'root'
})
export class ElectionService {
  private readonly API_URL = 'http://localhost:5000/electionalternative';
  private electionResults = new BehaviorSubject<ElectionResults | null>(null);
  private readonly POLLING_INTERVAL_ACTIVE = 3000; // 3 segundos quando ativa
  private readonly POLLING_INTERVAL_INACTIVE = 30000; // 30 segundos quando inativa
  
  public electionResults$ = this.electionResults.asObservable().pipe(
    tap(results => {
      console.log('[ElectionService] Observable emitindo dados:', results);
    })
  );
  private pollingSubscription: any;
  private lastKnownStatus: boolean | null = null;

  constructor(private http: HttpClient) {
    console.log('[ElectionService] Serviço construído');
  }

  private handleError(error: HttpErrorResponse) {
    console.error('[ElectionService] Erro na requisição HTTP:', error);
    if (error.error instanceof ErrorEvent) {
      console.error('[ElectionService] Erro do cliente:', error.error.message);
    } else {
      console.error(
        `[ElectionService] Backend retornou código ${error.status}, ` +
        `corpo: ${JSON.stringify(error.error)}`);
    }
    return of(null);
  }

  startElection(dados: any): Observable<any> {
    console.log('[ElectionService] Iniciando eleição com dados:', dados);
    this.lastKnownStatus = true; // Assume ativa ao iniciar
    return this.http.post(this.API_URL, dados).pipe(
      tap(response => console.log('[ElectionService] Resposta do POST:', response)),
      catchError(this.handleError.bind(this))
    );
  }

  startPolling() {
    console.log('[ElectionService] Iniciando polling');
    if (this.pollingSubscription) {
      console.log('[ElectionService] Cancelando polling anterior');
      this.pollingSubscription.unsubscribe();
    }

    // Faz uma requisição imediata
    this.fetchElectionData().subscribe();

    // Inicia o polling com intervalo inicial para eleição ativa
    this.pollingSubscription = timer(this.POLLING_INTERVAL_ACTIVE, this.POLLING_INTERVAL_ACTIVE).pipe(
      switchMap(() => {
        // Se sabemos que a eleição está inativa, usamos intervalo maior
        if (this.lastKnownStatus === false) {
          this.restartPollingWithLowerFrequency();
          return of(null);
        }
        return this.fetchElectionData();
      })
    ).subscribe();
  }

  private fetchElectionData(): Observable<ElectionResults | null> {
    console.log('[ElectionService] Fazendo requisição HTTP...');
    return this.http.get<any>(this.API_URL).pipe(
      map(response => {
        if (!response) return null;
        
        // Log da resposta bruta
        console.log('[ElectionService] Resposta bruta do servidor:', response);

        // Mapeia os campos do backend para o frontend
        const mappedResults: ElectionResults = {
          serialeleicao: response.serialeleicao,
          totalpopulacao: response.totalpopulacao,
          totalvotos: response.totalvotos,
          votos_por_partido: response.votos_por_partido,
          ativaeleicao: response.ativaeleicao,
          totalpossiveiseleitores: response.totalpossiveiseleitores
        };

        // Atualiza o status conhecido da eleição
        this.lastKnownStatus = mappedResults.ativaeleicao;

        console.log('[ElectionService] Dados mapeados:', mappedResults);
        return mappedResults;
      }),
      tap({
        next: (results) => {
          if (results) {
            console.log('[ElectionService] Dados válidos recebidos:', {
              serial: results.serialeleicao,
              ativa: results.ativaeleicao,
              votos: results.totalvotos,
              populacao: results.totalpopulacao,
              votos_por_partido: results.votos_por_partido
            });
            this.electionResults.next(results);
            console.log('[ElectionService] Dados emitidos para o BehaviorSubject');

            // Se a eleição não está mais ativa, reduz a frequência
            if (!results.ativaeleicao && this.lastKnownStatus !== false) {
              console.log('[ElectionService] Eleição finalizada, reduzindo frequência');
              this.restartPollingWithLowerFrequency();
            }
          }
        },
        error: (error) => {
          console.error('[ElectionService] Erro na requisição:', error);
          if (error.status !== 404) {
            this.handleError(error);
          }
        }
      }),
      catchError((error) => {
        if (error.status === 404) {
          console.log('[ElectionService] Nenhuma eleição em andamento (404)');
          return of(null);
        }
        return this.handleError(error);
      })
    );
  }

  private restartPollingWithLowerFrequency() {
    console.log('[ElectionService] Reiniciando polling com frequência reduzida');
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
    }
    
    this.pollingSubscription = timer(0, this.POLLING_INTERVAL_INACTIVE).pipe(
      switchMap(() => this.fetchElectionData())
    ).subscribe();
  }

  stopPolling() {
    console.log('[ElectionService] Parando polling');
    if (this.pollingSubscription) {
      this.pollingSubscription.unsubscribe();
      this.pollingSubscription = null;
    }
  }

  updateResults(results: ElectionResults) {
    console.log('[ElectionService] Atualizando resultados:', results);
    this.electionResults.next(results);
  }

  getResults(): Observable<ElectionResults | null> {
    return this.electionResults$;
  }
} 