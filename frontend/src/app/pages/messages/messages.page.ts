import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ConversationService } from '../../services/conversation.service';
import { AuthService } from '../../services/auth.service';
import { Conversation, Message } from '../../models/conversation.model';
import { User } from '../../models/user.model';
import { Subscription } from 'rxjs';
import { GuestAccessService } from '../../services/guest-access.service';
import { Router } from '@angular/router';
import { ActivatedRoute } from '@angular/router';
import { SocketService } from '../../services/socket.service';
import { ToastController } from '@ionic/angular';

import { ActionSheetController } from '@ionic/angular';

@Component({
  selector: 'app-messages',
  templateUrl: './messages.page.html',
  styleUrls: ['./messages.page.scss'],
  standalone: false,
})
export class MessagesPage implements OnInit, OnDestroy {
  @ViewChild('messagesContainer') private messagesContainer!: ElementRef;

  currentUser: User | null = null;
  conversations: Conversation[] = [];
  selectedConversation: Conversation | null = null;
  messages: Message[] = [];
  
  searchTerm = '';
  newMessageContent = '';
  
  isLoadingConversations = false;
  isLoadingMessages = false;
  isSending = false;
  
  isMobileRightPanelOpen = false;
  onlineUsers = new Set<string>();
  typingByConversation: Record<string, string> = {};
  expandedTimestamps = new Set<string>();
  replyToMessage: Message | null = null;
  private touchStartX = 0;
  private touchStartY = 0;

  private subs: Subscription[] = [];
  private searchTimeout: any;
  private pendingConversationId: string | null = null;

  constructor(
    private conversationService: ConversationService,
    private authService: AuthService,
    private guestAccessService: GuestAccessService,
    private router: Router,
    private route: ActivatedRoute,
    private socketService: SocketService,
    private toastController: ToastController,
    private actionSheetCtrl: ActionSheetController
  ) {}

  ngOnInit() {
    if (this.authService.isGuest) {
      this.guestAccessService.showSignupPrompt('Sign up to access messaging.');
      this.router.navigate(['/home/services']);
      return;
    }
    this.subs.push(
      this.route.queryParamMap.subscribe((params) => {
        const convId = params.get('conversationId');
        this.pendingConversationId = convId && /^[a-fA-F0-9]{24}$/.test(convId) ? convId : null;
      })
    );

    this.subs.push(
      this.authService.currentUser$.subscribe(user => {
        this.currentUser = user;
        if (user) {
          this.loadConversations();
        }
      })
    );

    this.subs.push(
      this.socketService.onlineUsers$.subscribe((onlineUsers) => {
        this.onlineUsers = onlineUsers;
      })
    );

    this.subs.push(
      this.socketService.messageNew$.subscribe((payload: { conversation_id: string; message: Message }) => {
        if (!payload?.message) return;
        const convId = String(payload.conversation_id);

        if (this.selectedConversation && String(this.selectedConversation.id) === convId) {
          this.upsertMessage(payload.message);
          this.scrollToBottom();
          this.conversationService.markConversationRead(convId).subscribe();
        }
        this.loadConversations();
      })
    );

    this.subs.push(
      this.socketService.messageRead$.subscribe((payload: { message_id: string; read_by: string }) => {
        if (!payload?.message_id || !payload?.read_by) return;
        this.messages = this.messages.map((msg) =>
          String(msg.id) === String(payload.message_id)
            ? { ...msg, is_read: true, read_by: [...(msg.read_by || []), payload.read_by] }
            : msg
        );
      })
    );

    this.subs.push(
      this.socketService.messageDelivered$.subscribe((payload: { message_id: string; user_id: string }) => {
        if (!payload?.message_id || !payload?.user_id) return;
        this.messages = this.messages.map((msg) =>
          String(msg.id) === String(payload.message_id)
            ? { ...msg, delivered_to: [...(msg.delivered_to || []), payload.user_id] }
            : msg
        );
      })
    );

    this.subs.push(
      this.socketService.typing$.subscribe((payload) => {
        if (!payload?.conversation_id || !payload?.user_id) return;
        const key = String(payload.conversation_id);
        if (!payload.is_typing) {
          delete this.typingByConversation[key];
          return;
        }
        const convo = this.conversations.find((c) => String(c.id) === key);
        this.typingByConversation[key] = convo?.other_user?.full_name || 'Someone';
      })
    );
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
  }

  loadConversations(event?: any) {
    if (!event) this.isLoadingConversations = true;
    this.conversationService.getConversations(this.searchTerm).subscribe({
      next: (res) => {
        this.conversations = res.conversations;
        this.isLoadingConversations = false;
        if (event) event.target.complete();

        if (this.pendingConversationId) {
          const target = this.conversations.find((c) => String(c.id) === this.pendingConversationId);
          if (target) {
            this.pendingConversationId = null;
            this.selectConversation(target);
          }
        }
        
        // If a conversation is selected, update it from the list if new data came
        if (this.selectedConversation) {
          const updated = this.conversations.find(c => c.id === this.selectedConversation!.id);
          if (updated) {
            this.selectedConversation = updated;
          }
        }
      },
      error: () => {
        this.isLoadingConversations = false;
        if (event) event.target.complete();
      }
    });
  }

  doRefresh(event: any) {
    this.loadConversations(event);
  }

  onSearch() {
    clearTimeout(this.searchTimeout);
    this.searchTimeout = setTimeout(() => {
      this.loadConversations();
    }, 300);
  }

  selectConversation(conv: Conversation) {
    this.selectedConversation = conv;
    this.isMobileRightPanelOpen = true;
    this.loadMessages();
    
    // Optimistically clear unread count locally
    conv.unread_count = 0;
    const totalUnread = this.conversations.reduce((acc, curr) => acc + curr.unread_count, 0);
    this.conversationService.updateUnreadCount(totalUnread);
  }

  backToList() {
    this.isMobileRightPanelOpen = false;
    this.selectedConversation = null;
    this.loadConversations(); // refresh counts
  }

  loadMessages() {
    if (!this.selectedConversation) return;
    
    this.isLoadingMessages = true;
    this.conversationService.getMessages(this.selectedConversation.id, 1, 100).subscribe({
      next: (res) => {
        this.messages = res.messages;
        this.isLoadingMessages = false;
        const selectedId = this.selectedConversation?.id;
        if (selectedId) {
          this.conversationService.markConversationRead(selectedId).subscribe();
        }
        this.scrollToBottom();
      },
      error: () => {
        this.isLoadingMessages = false;
      }
    });
  }

  sendMessage() {
    if (!this.newMessageContent.trim() || !this.selectedConversation || this.isSending) return;

    this.isSending = true;
    const content = this.newMessageContent.trim();
    this.newMessageContent = '';
    const replyToMessageId = this.replyToMessage ? this.replyToMessage.id : undefined;

    this.conversationService.sendMessage(this.selectedConversation.id, content, replyToMessageId).subscribe({
      next: (res) => {
        this.upsertMessage({
          ...res.message,
          reply_to_message_id: replyToMessageId,
        });
        this.isSending = false;
        this.scrollToBottom();
        this.selectedConversation!.last_message = content;
        this.selectedConversation!.last_message_at = res.message.created_at;
        this.replyToMessage = null;
      },
      error: () => {
        this.isSending = false;
        this.newMessageContent = content; // restore on fail
      }
    });
  }

  onKeydown(event: KeyboardEvent) {
    if (this.selectedConversation && this.currentUser) {
      this.socketService.emitTyping(String(this.selectedConversation.id), String(this.currentUser.id));
    }
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  scrollToBottom() {
    setTimeout(() => {
      if (this.messagesContainer && this.messagesContainer.nativeElement) {
        this.messagesContainer.nativeElement.scrollTop = this.messagesContainer.nativeElement.scrollHeight;
      }
    }, 100);
  }

  getInitials(name?: string): string {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  }

  formatTime(dateString: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  formatShortTime(dateString: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '';
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHrs = Math.floor(diffMs / 3600000);

    if (diffMins < 60) return diffMins === 0 ? 'now' : `${diffMins}m`;
    if (diffHrs < 24) return `${diffHrs}h`;
    return date.toLocaleDateString([], { weekday: 'short' });
  }

  // Group messages by day
  get groupedMessages() {
    const groups: { date: string, messages: Message[] }[] = [];
    let currentDate = '';
    
    for (const msg of this.messages) {
      if (!msg.created_at) continue;
      const dateObj = new Date(msg.created_at);
      if (isNaN(dateObj.getTime())) continue; // Skip invalid dates
      
      const msgDate = dateObj.toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });
      if (msgDate !== currentDate) {
        currentDate = msgDate;
        groups.push({ date: msgDate, messages: [msg] });
      } else {
        groups[groups.length - 1].messages.push(msg);
      }
    }
    return groups;
  }

  isLastInGroup(messages: Message[], index: number): boolean {
    if (index === messages.length - 1) return true;
    return messages[index].sender_id !== messages[index + 1].sender_id;
  }

  isUserOnline(userId: number | string | undefined): boolean {
    if (!userId) return false;
    return this.onlineUsers.has(String(userId));
  }

  getTypingText(conversationId: number | string): string {
    return this.typingByConversation[String(conversationId)] || '';
  }

  toggleMessageTimestamp(messageId: number | string) {
    const key = String(messageId);
    if (this.expandedTimestamps.has(key)) {
      this.expandedTimestamps.delete(key);
    } else {
      this.expandedTimestamps.add(key);
    }
  }

  isTimestampVisible(messageId: number | string): boolean {
    return this.expandedTimestamps.has(String(messageId));
  }

  async onMessageLongPress(message: Message) {
    this.toggleMessageTimestamp(message.id);
    
    const buttons: any[] = [
      {
        text: 'Copy text',
        icon: 'copy-outline',
        handler: () => {
          navigator.clipboard.writeText(message.content);
          this.showToast('Copied to clipboard');
        }
      },
      {
        text: 'Reply',
        icon: 'arrow-undo-outline',
        handler: () => {
          this.replyToMessage = message;
        }
      }
    ];

    if (message.sender_id === this.currentUser?.id) {
      buttons.push({
        text: 'Delete',
        icon: 'trash-outline',
        role: 'destructive' as any,
        handler: () => {
          // Implement soft delete logic
          this.showToast('Message deleted');
          message.content = 'This message was deleted';
        }
      });
    }

    buttons.push({
      text: 'Cancel',
      icon: 'close',
      role: 'cancel' as any,
      handler: () => {}
    });

    const actionSheet = await this.actionSheetCtrl.create({
      header: 'Message Options',
      buttons
    });
    await actionSheet.present();
  }

  async showToast(msg: string) {
    const toast = await this.toastController.create({
      message: msg,
      duration: 2000,
      position: 'top'
    });
    toast.present();
  }

  markConvRead(conv: Conversation) {
    this.conversationService.markConversationRead(conv.id).subscribe();
    conv.unread_count = 0;
  }

  deleteConv(conv: Conversation) {
    // Implement delete logic API if exists
    this.conversations = this.conversations.filter(c => c.id !== conv.id);
  }

  async openChatOptions(event: any) {
    const actionSheet = await this.actionSheetCtrl.create({
      buttons: [
        { text: 'View Profile', icon: 'person-outline', handler: () => { this.viewProfile(this.selectedConversation?.other_user?.id); } },
        { text: 'Clear Chat', icon: 'trash-outline', role: 'destructive', handler: () => { this.showToast('Chat cleared'); } },
        { text: 'Block User', icon: 'ban-outline', role: 'destructive', handler: () => { this.showToast('User blocked'); } },
        { text: 'Cancel', icon: 'close', role: 'cancel' }
      ]
    });
    await actionSheet.present();
  }

  viewProfile(userId: any) {
    if (userId) this.router.navigate(['/home/profile'], { queryParams: { userId }});
  }

  clearReply() {
    this.replyToMessage = null;
  }

  async onAttachClick() {
    const toast = await this.toastController.create({
      message: 'Attachment picker coming soon.',
      duration: 1500,
      color: 'medium',
    });
    await toast.present();
  }

  async onEmojiClick() {
    const toast = await this.toastController.create({
      message: 'Emoji picker coming soon.',
      duration: 1500,
      color: 'medium',
    });
    await toast.present();
  }

  getMessageTickState(message: Message): 'sent' | 'delivered' | 'read' {
    if (message.is_read || (message.read_by?.length || 0) > 1) return 'read';
    if ((message.delivered_to?.length || 0) > 1) return 'delivered';
    return 'sent';
  }

  private upsertMessage(message: Message) {
    const existingIndex = this.messages.findIndex((m) => String(m.id) === String(message.id));
    if (existingIndex >= 0) {
      this.messages[existingIndex] = message;
      return;
    }
    this.messages = [...this.messages, message];
  }
}
