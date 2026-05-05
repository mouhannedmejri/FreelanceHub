import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { OnboardingStateService } from '../../services/onboarding-state.service';

export interface WelcomeSlide {
  title: string;
  subtitle: string;
  description: string;
  image: string;
  icon: string;
  accentColor: string;
}

@Component({
  selector: 'app-welcome-slides',
  templateUrl: './welcome-slides.page.html',
  styleUrls: ['./welcome-slides.page.scss'],
  standalone: false,
})
export class WelcomeSlidesPage {
  currentIndex = 0;
  touchStartX = 0;
  touchEndX = 0;

  slides: WelcomeSlide[] = [
    {
      title: 'Find the Perfect Freelancer',
      subtitle: 'For Your Project',
      description: 'Browse thousands of skilled professionals ready to bring your vision to life. Filter by expertise, budget, and availability.',
      image: 'assets/onboarding/slide-1.png',
      icon: 'search-outline',
      accentColor: '#7c3aed',
    },
    {
      title: 'Showcase Your Skills',
      subtitle: 'And Get Hired',
      description: 'Build your professional profile, display your portfolio, and get discovered by clients looking for your unique talent.',
      image: 'assets/onboarding/slide-2.png',
      icon: 'star-outline',
      accentColor: '#9333ea',
    },
    {
      title: 'Secure Payments',
      subtitle: '& Real-Time Messaging',
      description: 'Communicate seamlessly with built-in messaging. Your transactions are protected with our escrow payment system.',
      image: 'assets/onboarding/slide-3.png',
      icon: 'shield-checkmark-outline',
      accentColor: '#22c55e',
    },
    {
      title: 'Browse Without',
      subtitle: 'Signing Up',
      description: 'Explore offers, services, and freelancer profiles freely. Sign up only when you\'re ready to take action.',
      image: 'assets/onboarding/slide-4.png',
      icon: 'eye-outline',
      accentColor: '#3b82f6',
    },
  ];

  constructor(
    private router: Router,
    private onboardingState: OnboardingStateService
  ) {}

  nextSlide() {
    if (this.currentIndex < this.slides.length - 1) {
      this.currentIndex++;
    } else {
      this.getStarted();
    }
  }

  prevSlide() {
    if (this.currentIndex > 0) {
      this.currentIndex--;
    }
  }

  goToSlide(index: number) {
    this.currentIndex = index;
  }

  async skip() {
    await this.onboardingState.markWelcomeCompleted();
    this.router.navigate(['/role-selection'], { replaceUrl: true });
  }

  async getStarted() {
    await this.onboardingState.markWelcomeCompleted();
    this.router.navigate(['/role-selection'], { replaceUrl: true });
  }

  get isLastSlide(): boolean {
    return this.currentIndex === this.slides.length - 1;
  }

  get buttonLabel(): string {
    return this.isLastSlide ? 'Get Started' : 'Next';
  }

  get buttonIcon(): string {
    return this.isLastSlide ? 'rocket-outline' : 'arrow-forward-outline';
  }

  get currentSlide(): WelcomeSlide {
    return this.slides[this.currentIndex];
  }

  // Touch gesture support
  onTouchStart(event: TouchEvent) {
    this.touchStartX = event.touches[0].clientX;
  }

  onTouchEnd(event: TouchEvent) {
    this.touchEndX = event.changedTouches[0].clientX;
    const diff = this.touchStartX - this.touchEndX;
    if (Math.abs(diff) > 50) {
      if (diff > 0) {
        this.nextSlide(); // swipe left → next
      } else {
        this.prevSlide(); // swipe right → prev
      }
    }
  }
}
