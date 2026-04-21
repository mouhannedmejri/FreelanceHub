import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../services/auth.service';

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

  constructor(private router: Router, private authService: AuthService) {}

  get selectedCount(): number {
    return this.interests.filter((i) => i.selected).length;
  }

  toggleInterest(interest: Interest) {
    interest.selected = !interest.selected;
  }

  skip() {
    this.router.navigate(['/home'], { replaceUrl: true });
  }

  continue() {
    // In a real app, we'd save these interests to the backend
    const selected = this.interests.filter((i) => i.selected).map((i) => i.name);
    console.log('Selected interests:', selected);
    this.router.navigate(['/home'], { replaceUrl: true });
  }
}
