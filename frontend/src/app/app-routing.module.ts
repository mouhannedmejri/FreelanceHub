import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';
import { RoleGuard } from './guards/role.guard';
import { GuestGuard } from './guards/guest.guard';

const routes: Routes = [
  {
    path: 'auth',
    loadChildren: () =>
      import('./pages/auth/auth.module').then((m) => m.AuthPageModule),
  },
  {
    path: 'onboarding',
    loadChildren: () =>
      import('./pages/onboarding/onboarding.module').then(
        (m) => m.OnboardingPageModule
      ),
    canActivate: [AuthGuard],
  },
  {
    path: 'home',
    loadChildren: () =>
      import('./pages/tabs/tabs.module').then((m) => m.TabsPageModule),
    canActivate: [GuestGuard],
  },
  {
    path: 'notifications',
    loadChildren: () =>
      import('./pages/notifications/notifications.module').then(
        (m) => m.NotificationsPageModule
      ),
    canActivate: [AuthGuard],
  },
  {
    path: 'publish-offer',
    loadChildren: () =>
      import('./pages/publish-offer/publish-offer.module').then(
        (m) => m.PublishOfferPageModule
      ),
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'offer-proposals/:id',
    loadChildren: () => import('./pages/offer-proposals/offer-proposals.module').then( m => m.OfferProposalsPageModule),
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'admin-dashboard',
    loadChildren: () => import('./pages/admin-dashboard/admin-dashboard.module').then( m => m.AdminDashboardPageModule),
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['admin'] }
  },
  {
    path: '',
    redirectTo: 'auth',
    pathMatch: 'full',
  },
  {
    path: 'client-dashboard',
    loadChildren: () => import('./pages/client-dashboard/client-dashboard.module').then( m => m.ClientDashboardPageModule),
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'project-detail/:id',
    loadChildren: () => import('./pages/project-detail/project-detail.module').then( m => m.ProjectDetailPageModule),
    canActivate: [AuthGuard],
  },
  {
    path: 'freelancer-dashboard',
    loadChildren: () => import('./pages/freelancer-dashboard/freelancer-dashboard.module').then( m => m.FreelancerDashboardPageModule),
    canActivate: [AuthGuard, RoleGuard],
    data: { roles: ['freelancer'] }
  },
  {
    path: 'search',
    loadChildren: () => import('./pages/search/search.module').then( m => m.SearchPageModule)
  }

];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule { }
