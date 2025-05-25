import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { FormsModule } from '@angular/forms';
import { ElectionAlternativeComponent } from './electionalternative.component';
import { ApiService } from '../../services/api.service';

describe('ElectionAlternativeComponent', () => {
  let component: ElectionAlternativeComponent;
  let fixture: ComponentFixture<ElectionAlternativeComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [
        ElectionAlternativeComponent,
        HttpClientTestingModule,
        FormsModule
      ],
      providers: [ApiService]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ElectionAlternativeComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('should validate population and votes', () => {
    component.populacao_total = 0;
    component.num_cidades = 0;
    component.startElection();
    expect(component.message).toContain('valores válidos maiores que zero');

    component.populacao_total = 10;
    component.num_cidades = 20;
    component.startElection();
    expect(component.message).toContain('não pode ser maior que a população total');
  });
});
