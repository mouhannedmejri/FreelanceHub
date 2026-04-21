import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { OfferService } from '../../services/offer.service';
import { CreateOfferPayload } from '../../models/offer.model';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-publish-offer',
  templateUrl: './publish-offer.page.html',
  styleUrls: ['./publish-offer.page.scss'],
  standalone: false,
})
export class PublishOfferPage implements OnInit {
  isSubmitting = false;
  submitError = '';
  submitSuccess = false;

  // Form fields
  title = '';
  description = '';
  selectedCategory = '';
  skillInput = '';
  skills: string[] = [];
  budgetMin: number | null = null;
  budgetMax: number | null = null;
  duration = '';
  selectedLocation = 'Remote';

  categories = [
    { label: 'Développement', value: 'Développement', icon: 'code-slash-outline' },
    { label: 'Design', value: 'Design', icon: 'color-palette-outline' },
    { label: 'Marketing', value: 'Marketing', icon: 'megaphone-outline' },
    { label: 'Rédaction', value: 'Rédaction', icon: 'document-text-outline' },
  ];

  durations = [
    '< 1 semaine',
    '1-4 semaines',
    '1-3 mois',
    '3-6 mois',
    '> 6 mois',
  ];

  locations = [
    { label: 'Remote', value: 'Remote', icon: 'globe-outline' },
    { label: 'Hybride', value: 'Hybrid', icon: 'git-network-outline' },
    { label: 'Sur site', value: 'Onsite', icon: 'business-outline' },
  ];

  constructor(
    private offerService: OfferService,
    private authService: AuthService,
    private router: Router
  ) {}

  ngOnInit() {}

  goBack() {
    this.router.navigate(['/home/store']);
  }

  selectCategory(value: string) {
    this.selectedCategory = value;
  }

  selectLocation(value: string) {
    this.selectedLocation = value;
  }

  onSkillKeydown(event: KeyboardEvent) {
    if (event.key === 'Enter' || event.key === ',') {
      event.preventDefault();
      this.addSkill();
    }
  }

  onSkillInput(event: Event) {
    const val = (event.target as HTMLInputElement).value;
    if (val.endsWith(',')) {
      this.addSkill();
    }
  }

  addSkill() {
    const skill = this.skillInput.replace(/,/g, '').trim();
    if (skill && !this.skills.includes(skill)) {
      this.skills = [...this.skills, skill];
    }
    this.skillInput = '';
  }

  removeSkill(skill: string) {
    this.skills = this.skills.filter((s) => s !== skill);
  }

  get isFormValid(): boolean {
    return (
      this.title.trim().length > 0 &&
      this.description.trim().length > 0 &&
      this.selectedCategory.length > 0 &&
      this.duration.length > 0
    );
  }

  submit() {
    if (!this.isFormValid || this.isSubmitting) return;

    this.isSubmitting = true;
    this.submitError = '';

    const payload: CreateOfferPayload = {
      title: this.title.trim(),
      description: this.description.trim(),
      category: this.selectedCategory,
      skills: this.skills,
      budget_min: this.budgetMin || 0,
      budget_max: this.budgetMax || 0,
      duration: this.duration,
      location: this.selectedLocation,
    };

    this.offerService.createOffer(payload).subscribe({
      next: () => {
        this.isSubmitting = false;
        this.submitSuccess = true;
        setTimeout(() => {
          this.router.navigate(['/home/store']);
        }, 1200);
      },
      error: (err) => {
        this.isSubmitting = false;
        this.submitError = err?.error?.error || 'Une erreur est survenue. Réessayez.';
      },
    });
  }
}
