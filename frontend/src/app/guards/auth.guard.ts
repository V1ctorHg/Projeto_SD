import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { ApiService } from '../services/api.service';
import { map, catchError, of } from 'rxjs';

export const authGuard = () => {
  const apiService = inject(ApiService);
  const router = inject(Router);

  // Verificar se há token no localStorage
  if (!apiService.isAuthenticated()) {
    router.navigate(['/login']);
    return of(false);
  }

  // Verificar se o token é válido no servidor
  return apiService.verifyToken().pipe(
    map(response => {
      if (response.valid) {
        return true;
      } else {
        apiService.logout();
        router.navigate(['/login']);
        return false;
      }
    }),
    catchError(() => {
      apiService.logout();
      router.navigate(['/login']);
      return of(false);
    })
  );
}; 