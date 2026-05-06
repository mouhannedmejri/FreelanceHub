import { NgModule } from '@angular/core';
import { PreloadAllModules, RouterModule, Routes } from '@angular/router';
import { AuthGuard } from './guards/auth.guard';
import { RoleGuard } from './guards/role.guard';
import { GuestAllowedGuard } from './guards/guest-allowed.guard';
import { AuthRequiredGuard } from './guards/auth-required.guard';
import { WelcomeGuard } from './guards/welcome.guard';

const routes: Routes = [
  {
    path: 'welcome',
    loadChildren: () =>
      import('./pages/welcome-slides/welcome-slides.module').then(
        (m) => m.WelcomeSlidesPageModule
      ),
  },
  {
    path: 'role-selection',
    loadChildren: () =>
      import('./pages/role-selection/role-selection.module').then(
        (m) => m.RoleSelectionPageModule
      ),
  },
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
    canActivate: [WelcomeGuard, GuestAllowedGuard],
  },
  {
    path: 'notifications',
    loadChildren: () =>
      import('./pages/notifications/notifications.module').then(
        (m) => m.NotificationsPageModule
      ),
    canActivate: [AuthRequiredGuard],
  },
  {
    path: 'publish-offer',
    loadChildren: () =>
      import('./pages/publish-offer/publish-offer.module').then(
        (m) => m.PublishOfferPageModule
      ),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'offer-proposals/:id',
    loadChildren: () => import('./pages/offer-proposals/offer-proposals.module').then( m => m.OfferProposalsPageModule),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'admin-dashboard',
    loadChildren: () => import('./pages/admin-dashboard/admin-dashboard.module').then( m => m.AdminDashboardPageModule),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['admin'] }
  },
  {
    path: '',
    redirectTo: 'home',
    pathMatch: 'full',
  },
  {
    path: 'client-dashboard',
    loadChildren: () => import('./pages/client-dashboard/client-dashboard.module').then( m => m.ClientDashboardPageModule),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['client'] }
  },
  {
    path: 'project-detail/:id',
    loadChildren: () => import('./pages/project-detail/project-detail.module').then( m => m.ProjectDetailPageModule),
    canActivate: [AuthRequiredGuard],
  },
  {
    path: 'freelancer-dashboard',
    loadChildren: () => import('./pages/freelancer-dashboard/freelancer-dashboard.module').then( m => m.FreelancerDashboardPageModule),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['freelancer'] }
  },
  {
    path: 'search',
    loadChildren: () => import('./pages/freelancer-search/freelancer-search.module').then( m => m.FreelancerSearchPageModule),
    canActivate: [GuestAllowedGuard]
  },
  {
    path: 'freelancer-search',
    loadChildren: () => import('./pages/freelancer-search/freelancer-search.module').then( m => m.FreelancerSearchPageModule),
    canActivate: [GuestAllowedGuard]
  },
  {
    path: 'freelancer/:username',
    loadChildren: () => import('./pages/profile/profile.module').then( m => m.ProfilePageModule),
    canActivate: [GuestAllowedGuard]
  },
  {
    path: 'seller-dashboard',
    loadChildren: () => import('./pages/seller-dashboard/seller-dashboard.module').then( m => m.SellerDashboardPageModule),
    canActivate: [AuthRequiredGuard, RoleGuard],
    data: { roles: ['freelancer'] }
  },
  {
    path: 'my-purchases',
    loadChildren: () => import('./pages/my-purchases/my-purchases.module').then( m => m.MyPurchasesPageModule),
    canActivate: [AuthRequiredGuard]
  },
  {
    path: 'digital-store',
    loadChildren: () => import('./pages/digital-store/digital-store.module').then( m => m.DigitalStorePageModule),
    canActivate: [GuestAllowedGuard]
    
  },
  {
    path: 'pricing',
    loadChildren: () => import('./pages/pricing/pricing.module').then( m => m.PricingPageModule)
  }


];

@NgModule({
  imports: [
    RouterModule.forRoot(routes, { preloadingStrategy: PreloadAllModules }),
  ],
  exports: [RouterModule],
})
export class AppRoutingModule { }
