import { Component, EventEmitter, Input, Output } from '@angular/core';
import { ImageUploadService } from '../../services/image-upload.service';

@Component({
  selector: 'app-add-portfolio-project-modal',
  templateUrl: './add-portfolio-project-modal.component.html',
  styleUrls: ['./add-portfolio-project-modal.component.scss'],
  standalone: false,
})
export class AddPortfolioProjectModalComponent {
  @Input() isOpen = false;
  @Input() initialData: any = null;
  @Output() dismissed = new EventEmitter<void>();
  @Output() saved = new EventEmitter<any>();

  form: any = {
    title: '', description: '', category: '', technologiesText: '',
    project_url: '', github_url: '', completed_date: '', client_name: '', is_featured: false,
  };
  images: File[] = [];
  previews: string[] = [];

  constructor(private imageUploadService: ImageUploadService) {}

  ngOnChanges(): void {
    if (this.initialData) {
      this.form = {
        title: this.initialData.title || '',
        description: this.initialData.description || '',
        category: this.initialData.category || '',
        technologiesText: (this.initialData.technologies || []).join(', '),
        project_url: this.initialData.project_url || '',
        github_url: this.initialData.github_url || '',
        completed_date: this.initialData.completed_date || '',
        client_name: this.initialData.client_name || '',
        is_featured: !!this.initialData.is_featured,
      };
      this.previews = this.initialData.images || [];
      this.images = [];
    }
  }

  async onFilesSelected(event: any): Promise<void> {
    const selected: File[] = Array.from(event.target.files || []);
    for (const file of selected) {
      const err = this.imageUploadService.validateFile(file);
      if (err) continue;
      const compressed = await this.imageUploadService.compressImage(file);
      this.images.push(compressed);
      this.previews.push(this.imageUploadService.createObjectPreview(compressed));
    }
  }

  moveImage(index: number, dir: -1 | 1): void {
    const target = index + dir;
    if (target < 0 || target >= this.previews.length) return;
    [this.previews[index], this.previews[target]] = [this.previews[target], this.previews[index]];
    if (this.images.length) {
      [this.images[index], this.images[target]] = [this.images[target], this.images[index]];
    }
  }

  submit(): void {
    const payload = {
      ...this.form,
      technologies: String(this.form.technologiesText || '').split(',').map((s: string) => s.trim()).filter(Boolean),
    };
    this.saved.emit({ payload, images: this.images });
  }
}

