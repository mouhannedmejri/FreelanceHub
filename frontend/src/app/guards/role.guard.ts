import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot): boolean {
    const expectedRoles = route.data['roles'] as string[];
    const currentUser = this.authService.currentUser;

    if (!currentUser) {
      this.router.navigate(['/auth']);
      return false;
    }

    if (expectedRoles && expectedRoles.indexOf(currentUser.role) === -1) {
      this.router.navigate(['/home']);
      return false;
    }

    return true;
  }
}
