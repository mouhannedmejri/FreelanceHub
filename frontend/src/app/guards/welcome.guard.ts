import { Injectable } from '@angular/core';
import { CanActivate, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { OnboardingStateService } from '../services/onboarding-state.service';

/**
 * WelcomeGuard — redirects first-time visitors to the welcome slides.
 *
 * If the user has already completed the welcome slides or is authenticated,
 * they pass through to the requested route. Otherwise, they are redirected
 * to the welcome-slides page.
 */
@Injectable({ providedIn: 'root' })
export class WelcomeGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private onboardingState: OnboardingStateService,
    private router: Router
  ) {}

  canActivate(): boolean {
    // Authenticated users skip welcome
    if (this.authService.isAuthenticated) {
      return true;
    }

    // Already completed welcome? Let through
    if (this.onboardingState.isWelcomeCompleted) {
      return true;
    }

    // First-time visitor → show welcome slides
    this.router.navigate(['/welcome'], { replaceUrl: true });
    return false;
  }
}
