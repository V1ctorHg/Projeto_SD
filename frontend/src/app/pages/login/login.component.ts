import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent {
  username: string = '';
  password: string = '';
  loading: boolean = false;
  error: string = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  async onSubmit() {
    if (!this.username || !this.password) {
      this.error = 'Por favor, preencha todos os campos';
      return;
    }

    this.loading = true;
    this.error = '';

    this.apiService.login(this.username, this.password).subscribe({
      next: (response) => {
        if (response.access_token) {
          // Salvar token no localStorage
          localStorage.setItem('access_token', response.access_token);
          localStorage.setItem('username', response.username);
          
          // Redirecionar para o dashboard
          this.router.navigate(['/dashboard']);
        }
      },
      error: (error) => {
        console.error('Erro no login:', error);
        this.error = error.error?.erro || 'Erro ao fazer login. Tente novamente.';
        this.loading = false;
      },
      complete: () => {
        this.loading = false;
      }
    });
  }
} 