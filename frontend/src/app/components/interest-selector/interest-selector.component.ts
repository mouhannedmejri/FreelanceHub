import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-interest-selector',
  templateUrl: './interest-selector.component.html',
  styleUrls: ['./interest-selector.component.scss'],
  standalone: false,
})
export class InterestSelectorComponent {
  @Input() selectedInterests: string[] = [];
  @Input() compact = false;
  @Output() selectedInterestsChange = new EventEmitter<string[]>();

  readonly interestGroups = [
    { label: 'Technology', items: ['Web Dev', 'Mobile Dev', 'Software Engineering', 'DevOps'] },
    { label: 'Design', items: ['UI/UX', 'Graphic Design', 'Logo Design', 'Illustration'] },
    { label: 'Content', items: ['Writing', 'Translation', 'Copywriting', 'Proofreading'] },
    { label: 'Marketing', items: ['SEO', 'Social Media', 'Email Marketing', 'Advertising'] },
    { label: 'Video', items: ['Editing', 'Animation', 'Production'] },
    { label: 'Business', items: ['Consulting', 'Data Entry', 'Virtual Assistant'] },
  ];

  toggle(interest: string): void {
    const exists = this.selectedInterests.includes(interest);
    const next = exists
      ? this.selectedInterests.filter((i) => i !== interest)
      : [...this.selectedInterests, interest];
    this.selectedInterests = next;
    this.selectedInterestsChange.emit(next);
  }

  isSelected(interest: string): boolean {
    return this.selectedInterests.includes(interest);
  }
}
