import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FormularioVotacaoComponent } from './formulario-votacao.component';

describe('FormularioVotacaoComponent', () => {
  let component: FormularioVotacaoComponent;
  let fixture: ComponentFixture<FormularioVotacaoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [FormularioVotacaoComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(FormularioVotacaoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
