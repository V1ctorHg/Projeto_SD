import { TestBed } from '@angular/core/testing';

import { VotacaoService } from './votacao.service';

describe('VotacaoService', () => {
  let service: VotacaoService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(VotacaoService);
  });

  it('should be created', () => {
    expect(service).toBeTruthy();
  });
});
