import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  username = '';

  constructor(
    private apiService: ApiService,
    private router: Router
  ) {}

  ngOnInit() {
    this.username = localStorage.getItem('username') || '';
  }

  logout() {
    this.apiService.logout();
    this.router.navigate(['/login']);
  }

  navigateToVote() {
    this.router.navigate(['/vote']);
  }

  navigateToResults() {
    this.router.navigate(['/results']);
  }

  navigateToElectionAlternative() {
    this.router.navigate(['/electionalternative']);
  }
} 