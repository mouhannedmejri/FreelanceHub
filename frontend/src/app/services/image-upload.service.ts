import { Injectable } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ImageUploadService {
  private readonly maxBytes = 5 * 1024 * 1024;
  private readonly allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];

  validateFile(file: File): string | null {
    if (!this.allowedTypes.includes(file.type)) {
      return 'Only JPG, PNG, GIF, WebP are allowed.';
    }
    if (file.size > this.maxBytes) {
      return 'Each image must be <= 5MB.';
    }
    return null;
  }

  async compressImage(file: File, quality = 0.82, maxWidth = 1600): Promise<File> {
    if (!file.type.startsWith('image/')) return file;

    const dataUrl = await this.readAsDataURL(file);
    const img = await this.loadImage(dataUrl);
    const canvas = document.createElement('canvas');

    const ratio = img.width > maxWidth ? maxWidth / img.width : 1;
    canvas.width = Math.round(img.width * ratio);
    canvas.height = Math.round(img.height * ratio);

    const ctx = canvas.getContext('2d');
    if (!ctx) return file;
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise<Blob | null>((resolve) =>
      canvas.toBlob(resolve, file.type === 'image/png' ? 'image/png' : 'image/jpeg', quality)
    );

    if (!blob) return file;
    const ext = file.type === 'image/png' ? 'png' : 'jpg';
    const baseName = file.name.replace(/\.[^/.]+$/, '');
    return new File([blob], `${baseName}.${ext}`, { type: blob.type });
  }

  createObjectPreview(file: File): string {
    return URL.createObjectURL(file);
  }

  private readAsDataURL(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  }

  private loadImage(src: string): Promise<HTMLImageElement> {
    return new Promise((resolve, reject) => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = reject;
      img.src = src;
    });
  }
}

