import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { OnboardingStateService, UserIntent } from '../../services/onboarding-state.service';

interface RoleOption {
  intent: UserIntent;
  icon: string;
  title: string;
  subtitle: string;
  description: string;
  gradient: string;
  accentColor: string;
  badgeText: string;
}

@Component({
  selector: 'app-role-selection',
  templateUrl: './role-selection.page.html',
  styleUrls: ['./role-selection.page.scss'],
  standalone: false,
})
export class RoleSelectionPage {
  selectedIntent: UserIntent = null;

  options: RoleOption[] = [
    {
      intent: 'hiring',
      icon: 'briefcase-outline',
      title: 'I\'m Hiring',
      subtitle: 'Client',
      description: 'Post projects and find the perfect freelancer for your needs.',
      gradient: 'linear-gradient(135deg, #7c3aed, #a855f7)',
      accentColor: '#7c3aed',
      badgeText: 'Popular',
    },
    {
      intent: 'freelancing',
      icon: 'rocket-outline',
      title: 'I\'m Freelancing',
      subtitle: 'Freelancer',
      description: 'Showcase your skills, get hired, and grow your career.',
      gradient: 'linear-gradient(135deg, #059669, #10b981)',
      accentColor: '#10b981',
      badgeText: 'Most Chosen',
    },
    {
      intent: 'browsing',
      icon: 'compass-outline',
      title: 'Just Browsing',
      subtitle: 'Explorer',
      description: 'Look around freely. No account needed to discover opportunities.',
      gradient: 'linear-gradient(135deg, #2563eb, #3b82f6)',
      accentColor: '#3b82f6',
      badgeText: 'No Sign-up',
    },
  ];

  constructor(
    private router: Router,
    private authService: AuthService,
    private onboardingState: OnboardingStateService
  ) {}

  selectOption(option: RoleOption) {
    this.selectedIntent = option.intent;
  }

  async continueWithSelection() {
    if (!this.selectedIntent) return;

    await this.onboardingState.setIntent(this.selectedIntent);

    if (this.selectedIntent === 'browsing') {
      // Go straight to main app as guest
      this.authService.enterGuestMode();
      this.router.navigate(['/home'], { replaceUrl: true });
    } else {
      // Go to auth page with pre-selected role
      const role = this.selectedIntent === 'hiring' ? 'client' : 'freelancer';
      this.router.navigate(['/auth'], {
        queryParams: { tab: 'register', role },
        replaceUrl: true,
      });
    }
  }

  async browseAsGuest() {
    await this.onboardingState.setIntent('browsing');
    this.authService.enterGuestMode();
    this.router.navigate(['/home'], { replaceUrl: true });
  }

  goToLogin() {
    this.router.navigate(['/auth'], {
      queryParams: { tab: 'login' },
      replaceUrl: true,
    });
  }
}
