import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { IonicModule } from '@ionic/angular';
import { MessagesPage } from './messages.page';
import { MessagesPageRoutingModule } from './messages-routing.module';

@NgModule({
  imports: [CommonModule, IonicModule, MessagesPageRoutingModule],
  declarations: [MessagesPage],
})
export class MessagesPageModule {}
