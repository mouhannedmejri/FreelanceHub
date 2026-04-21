import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { NotificationsPage } from './notifications.page';
import { NotificationsPageRoutingModule } from './notifications-routing.module';

@NgModule({
    imports: [CommonModule, IonicModule, NotificationsPageRoutingModule],
    declarations: [NotificationsPage],
})
export class NotificationsPageModule { }
