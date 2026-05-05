import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * AuthGuard — strict authentication check.
 *
 * Use this guard only for routes that MUST have authentication
 * before they can render (e.g., onboarding).
 *
 * For routes where guests should see an auth modal instead of
 * a hard redirect, use AuthRequiredGuard.
 */
@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {
    if (this.authService.isAuthenticated) {
      return true;
    }
    this.router.navigate(['/auth']);
    return false;
  }
}
