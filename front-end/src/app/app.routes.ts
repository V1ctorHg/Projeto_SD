import { Routes } from '@angular/router';
import { VoteComponent } from './pages/vote/vote.component';
import { ResultsComponent } from './pages/results/results.component';

export const routes: Routes = [
    { path: '', redirectTo: 'vote', pathMatch: 'full' },
    { path: 'vote', component: VoteComponent },
    { path: 'results', component: ResultsComponent }
];
