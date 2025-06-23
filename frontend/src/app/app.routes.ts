import { Routes } from '@angular/router';
import { VoteComponent } from './pages/vote/vote.component';
import { ResultsComponent } from './pages/results/results.component';
import { ElectionAlternativeComponent } from './pages/electionalternative/electionalternative.component';
import { LoginComponent } from './pages/login/login.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
    { path: '', redirectTo: 'login', pathMatch: 'full' },
    { path: 'login', component: LoginComponent },
    { path: 'dashboard', component: DashboardComponent, canActivate: [authGuard] },
    { path: 'vote', component: VoteComponent, canActivate: [authGuard] },
    { path: 'results', component: ResultsComponent, canActivate: [authGuard] },
    { path: 'electionalternative', component: ElectionAlternativeComponent, canActivate: [authGuard] }
];
