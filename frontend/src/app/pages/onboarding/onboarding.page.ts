import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';
import { ProfileService } from '../../services/profile.service';
import { ToastController } from '@ionic/angular';

interface Interest {
  name: string;
  icon: string;
  selected: boolean;
}

@Component({
  selector: 'app-onboarding',
  templateUrl: './onboarding.page.html',
  styleUrls: ['./onboarding.page.scss'],
  standalone: false,
})
export class OnboardingPage {
  step = 1;
  readonly totalSteps = 4;

  interests: Interest[] = [
    { name: 'Développement Web', icon: 'code-slash-outline', selected: false },
    { name: 'Design UI/UX', icon: 'color-palette-outline', selected: false },
    { name: 'Mobile App', icon: 'phone-portrait-outline', selected: false },
    { name: 'Data Science', icon: 'analytics-outline', selected: false },
    { name: 'Marketing Digital', icon: 'megaphone-outline', selected: false },
    { name: 'Rédaction', icon: 'document-text-outline', selected: false },
    { name: 'Vidéo & Animation', icon: 'videocam-outline', selected: false },
    { name: 'DevOps & Cloud', icon: 'cloud-outline', selected: false },
    { name: 'Cybersécurité', icon: 'shield-checkmark-outline', selected: false },
    { name: 'IA & Machine Learning', icon: 'hardware-chip-outline', selected: false },
    { name: 'Blockchain', icon: 'link-outline', selected: false },
    { name: 'Consulting', icon: 'people-outline', selected: false },
  ];

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
    return this.interests.filter((i) => i.selected).length;
  }

  toggleInterest(interest: Interest) {
    if (!interest.selected && this.selectedCount >= 5) {
      return;
    }
    interest.selected = !interest.selected;
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
    if (this.step === 2 && (this.selectedCount < 3 || this.selectedCount > 5)) {
      this.showToast('Select between 3 and 5 skills/interests');
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
      skills_or_interests: this.interests.filter((i) => i.selected).map((i) => i.name),
      budget_or_rate: this.budgetOrRate,
      notifications: this.notificationPreferences,
    };

    this.profileService
      .updateOnboardingPreferences({
        preferences,
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
