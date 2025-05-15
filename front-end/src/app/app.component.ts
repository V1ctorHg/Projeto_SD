import { Component } from '@angular/core';
import { RouterModule, RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';
import { Router, Route } from '@angular/router';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet, RouterModule, CommonModule],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'Sistema de Votação';

  constructor(private router: Router) {
    console.log('Rotas configuradas:');
    this.logRoutes(this.router.config);
  }

  logRoutes(routes: Route[], prefix: string = ''): void {
    for (const route of routes) {
      const path = prefix + (route.path ? '/' + route.path : '');
      console.log(path || '/');
      if (route.children) {
        this.logRoutes(route.children, path);
      }
    }
  }
}