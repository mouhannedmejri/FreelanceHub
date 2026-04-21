import { Component, Input } from '@angular/core';
import { ModalController } from '@ionic/angular';

@Component({
  selector: 'app-leave-review',
  templateUrl: './leave-review.component.html',
  styleUrls: ['./leave-review.component.scss'],
  standalone: false,
})
export class LeaveReviewComponent {
  @Input() targetUserId!: number;
  rating: number = 0;
  comment: string = '';

  constructor(private modalController: ModalController) {}

  setRating(val: number) {
    this.rating = val;
  }

  cancel() {
    this.modalController.dismiss();
  }

  submit() {
    if (this.rating > 0 && this.comment.trim()) {
      this.modalController.dismiss({
        rating: this.rating,
        comment: this.comment
      }, 'confirm');
    }
  }
}
