import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * GuestGuard — allows both authenticated and guest users.
 * If the user is not authenticated and not in guest mode,
 * automatically enters guest mode instead of redirecting to auth.
 *
 * NOTE: This guard is kept for backward compatibility.
 * For new routes, prefer using GuestAllowedGuard (always passes)
 * or AuthRequiredGuard (shows auth modal).
 */
@Injectable({
  providedIn: 'root',
})
export class GuestGuard implements CanActivate {
  constructor(private authService: AuthService, private router: Router) {}

  canActivate(): boolean {
    if (this.authService.isAuthenticated) {
      return true;
    }
    // Auto-enter guest mode instead of blocking
    if (!this.authService.isGuest) {
      this.authService.enterGuestMode();
    }
    return true;
  }
}
