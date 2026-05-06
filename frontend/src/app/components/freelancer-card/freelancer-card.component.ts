import { Component, EventEmitter, Input, Output } from '@angular/core';

@Component({
  selector: 'app-freelancer-card',
  templateUrl: './freelancer-card.component.html',
  styleUrls: ['./freelancer-card.component.scss'],
  standalone: false,
})
export class FreelancerCardComponent {
  @Input() freelancer: any;
  @Output() viewProfile = new EventEmitter<any>();
  @Output() contact = new EventEmitter<any>();

  onViewProfile(): void {
    this.viewProfile.emit(this.freelancer);
  }

  onContact(): void {
    this.contact.emit(this.freelancer);
  }

  trackByThumb(_: number, thumb: string): string {
    return thumb;
  }
}
