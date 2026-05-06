import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ProfileService } from '../../services/profile.service';
import { ToastController } from '@ionic/angular';

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.page.html',
  styleUrls: ['./onboarding.page.scss'],
  standalone: false,
})
export class OnboardingPage {
  step = 1;
  readonly totalSteps = 4;

  interests: string[] = [];
  roleGoal: 'client' | 'freelancer' = 'freelancer';
  budgetOrRate = 60;
  notificationPreferences = {
    proposals: true,
    messages: true,
    marketing: false,
    product_updates: true,
  };

  constructor(
    private router: Router,
    private authService: AuthService,
    private profileService: ProfileService,
    private toastCtrl: ToastController
  ) {}

  get selectedCount(): number {
    return this.interests.length;
  }

  selectRole(role: 'client' | 'freelancer') {
    this.roleGoal = role;
  }

  skip() {
    if (this.step < this.totalSteps) {
      this.step++;
      return;
    }
    this.finishOnboarding();
  }

  continue() {
    if (this.step === 2 && this.roleGoal === 'client' && (this.selectedCount < 3 || this.selectedCount > 8)) {
      this.showToast('Select between 3 and 8 interests');
      return;
    }
    if (this.step < this.totalSteps) {
      this.step++;
      return;
    }
    this.finishOnboarding();
  }

  private finishOnboarding() {
    const preferences = {
      role_goal: this.roleGoal,
      skills_or_interests: this.interests,
      budget_or_rate: this.budgetOrRate,
      notifications: this.notificationPreferences,
    };

    this.profileService
      .updateOnboardingPreferences({
        preferences,
        interests: this.roleGoal === 'client' ? this.interests : [],
        onboarding_complete: true,
      })
      .subscribe({
        next: async (res) => {
          await this.authService.setCurrentUser(res.user);
          this.router.navigate(['/home'], { replaceUrl: true });
        },
        error: () => {
          this.showToast('Unable to save onboarding now');
          this.router.navigate(['/home'], { replaceUrl: true });
        },
      });
  }

  get progress(): number {
    return Math.round((this.step / this.totalSteps) * 100);
  }

  get isLastStep(): boolean {
    return this.step === this.totalSteps;
  }

  get continueLabel(): string {
    return this.isLastStep ? 'Finish' : 'Next';
  }

  get rateLabel(): string {
    return this.roleGoal === 'client'
      ? `Budget preference: ${this.budgetOrRate}€/h`
      : `Rate preference: ${this.budgetOrRate}€/h`;
  }

  private async showToast(message: string) {
    const toast = await this.toastCtrl.create({
      message,
      duration: 2200,
      color: 'warning',
    });
    await toast.present();
  }
}
