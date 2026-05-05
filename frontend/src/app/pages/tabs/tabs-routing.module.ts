import { NgModule } from '@angular/core';
import { RouterModule, Routes } from '@angular/router';
import { TabsPage } from './tabs.page';
import { GuestAllowedGuard } from '../../guards/guest-allowed.guard';
import { AuthRequiredGuard } from '../../guards/auth-required.guard';

const routes: Routes = [
  {
    path: '',
    component: TabsPage,
    children: [
      {
        path: 'dashboard',
        loadChildren: () =>
          import('../../home/home.module').then((m) => m.HomePageModule),
        canActivate: [GuestAllowedGuard],
      },
      {
        path: 'search',
        loadChildren: () =>
          import('../search/search.module').then(
            (m) => m.SearchPageModule
          ),
        canActivate: [GuestAllowedGuard],
      },
      {
        path: 'messages',
        loadChildren: () =>
          import('../messages/messages.module').then(
            (m) => m.MessagesPageModule
          ),
        canActivate: [AuthRequiredGuard],
      },
      {
        path: 'store',
        loadChildren: () =>
          import('../store/store.module').then((m) => m.StorePageModule),
        canActivate: [GuestAllowedGuard],
      },
      {
        path: 'digital-store',
        loadChildren: () =>
          import('../digital-store/digital-store.module').then((m) => m.DigitalStorePageModule),
        canActivate: [GuestAllowedGuard],
      },
      {
        path: 'profile',
        loadChildren: () =>
          import('../profile/profile.module').then(
            (m) => m.ProfilePageModule
          ),
        canActivate: [GuestAllowedGuard],
      },
      {
        path: '',
        redirectTo: 'dashboard',
        pathMatch: 'full',
      },
    ],
  },
];

@NgModule({
  imports: [RouterModule.forChild(routes)],
  exports: [RouterModule],
})
export class TabsPageRoutingModule {}
