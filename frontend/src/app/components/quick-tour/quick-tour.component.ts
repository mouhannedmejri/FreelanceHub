import { Component, Input, OnInit } from '@angular/core';
import { ModalController } from '@ionic/angular';
import { OnboardingStateService } from '../../services/onboarding-state.service';

interface TourStep {
  icon: string;
  title: string;
  description: string;
  gradient: string;
  tip: string;
}

@Component({
  selector: 'app-quick-tour',
  templateUrl: './quick-tour.component.html',
  styleUrls: ['./quick-tour.component.scss'],
  standalone: false,
})
export class QuickTourComponent implements OnInit {
  @Input() startStep = 0;

  currentStep = 0;

  steps: TourStep[] = [
    {
      icon: 'home-outline',
      title: 'Home Dashboard',
      description: 'Your personalized feed with recommended offers, platform stats, and quick access to all features.',
      gradient: 'linear-gradient(135deg, #7c3aed, #a855f7)',
      tip: 'Swipe through job cards to discover opportunities matching your skills.',
    },
    {
      icon: 'search-outline',
      title: 'Browse & Search',
      description: 'Find freelancers, offers, and services using our powerful search. Filter by category, budget, and expertise.',
      gradient: 'linear-gradient(135deg, #2563eb, #3b82f6)',
      tip: 'Use the search tab to explore all available projects and talent.',
    },
    {
      icon: 'person-outline',
      title: 'Freelancer Profiles',
      description: 'View detailed profiles with portfolios, ratings, reviews, and availability. Follow freelancers you like.',
      gradient: 'linear-gradient(135deg, #059669, #10b981)',
      tip: 'Tap any freelancer card to see their full profile and work history.',
    },
    {
      icon: 'storefront-outline',
      title: 'Services & Store',
      description: 'Browse pre-packaged services and digital products. Discover tools and resources from the community.',
      gradient: 'linear-gradient(135deg, #ea580c, #f97316)',
      tip: 'Check the Store tab for digital products and the Services marketplace.',
    },
    {
      icon: 'chatbubble-outline',
      title: 'Messaging',
      description: 'Real-time conversations with clients and freelancers. Track read receipts and stay connected.',
      gradient: 'linear-gradient(135deg, #7c3aed, #c084fc)',
      tip: 'Messages are available once you create an account.',
    },
  ];

  constructor(
    private modalCtrl: ModalController,
    private onboardingState: OnboardingStateService
  ) {}

  ngOnInit() {
    this.currentStep = this.startStep;
  }

  nextStep() {
    if (this.currentStep < this.steps.length - 1) {
      this.currentStep++;
    } else {
      this.finish();
    }
  }

  prevStep() {
    if (this.currentStep > 0) {
      this.currentStep--;
    }
  }

  goToStep(index: number) {
    this.currentStep = index;
  }

  async finish() {
    await this.onboardingState.markTourCompleted();
    this.modalCtrl.dismiss({ completed: true });
  }

  async skip() {
    await this.onboardingState.markTourCompleted();
    this.modalCtrl.dismiss({ completed: false });
  }

  get isLastStep(): boolean {
    return this.currentStep === this.steps.length - 1;
  }

  get isFirstStep(): boolean {
    return this.currentStep === 0;
  }

  get currentStepData(): TourStep {
    return this.steps[this.currentStep];
  }

  get progress(): number {
    return ((this.currentStep + 1) / this.steps.length) * 100;
  }
}
