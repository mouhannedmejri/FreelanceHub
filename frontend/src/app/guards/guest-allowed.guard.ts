import { Injectable } from '@angular/core';
import { CanActivate } from '@angular/router';

/**
 * GuestAllowedGuard – always returns true.
 *
 * Applied to public-browsable routes (offers list, services, store,
 * freelancer profiles, individual offer/service details).
 * Both authenticated users and unauthenticated guests pass through.
 */
@Injectable({ providedIn: 'root' })
export class GuestAllowedGuard implements CanActivate {
  canActivate(): boolean {
    return true;
  }
}
