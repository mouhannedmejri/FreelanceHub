import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ConversationService } from '../../services/conversation.service';
import { AuthService } from '../../services/auth.service';
import { Conversation, Message } from '../../models/conversation.model';
import { User } from '../../models/user.model';
import { Subscription } from 'rxjs';
import { GuestAccessService } from '../../services/guest-access.service';
import { Router } from '@angular/router';
import { SocketService } from '../../services/socket.service';
import { ToastController } from '@ionic/angular';

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

  constructor(
    private conversationService: ConversationService,
    private authService: AuthService,
    private guestAccessService: GuestAccessService,
    private router: Router,
    private socketService: SocketService,
    private toastController: ToastController
  ) {}

  ngOnInit() {
    if (this.authService.isGuest) {
      this.guestAccessService.showSignupPrompt('Sign up to access messaging.');
      this.router.navigate(['/home/services']);
      return;
    }
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

  loadConversations() {
    this.isLoadingConversations = true;
    this.conversationService.getConversations(this.searchTerm).subscribe({
      next: (res) => {
        this.conversations = res.conversations;
        this.isLoadingConversations = false;
        
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
      }
    });
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

  getInitials(name: string): string {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  }

  formatTime(dateString: string): string {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Group messages by day
  get groupedMessages() {
    const groups: { date: string, messages: Message[] }[] = [];
    let currentDate = '';
    
    for (const msg of this.messages) {
      const msgDate = new Date(msg.created_at).toLocaleDateString([], { weekday: 'long', day: 'numeric', month: 'long' });
      if (msgDate !== currentDate) {
        currentDate = msgDate;
        groups.push({ date: msgDate, messages: [msg] });
      } else {
        groups[groups.length - 1].messages.push(msg);
      }
    }
    return groups;
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

  onMessageTouchStart(event: TouchEvent) {
    const touch = event.changedTouches[0];
    this.touchStartX = touch.clientX;
    this.touchStartY = touch.clientY;
  }

  onMessageTouchEnd(event: TouchEvent, message: Message) {
    const touch = event.changedTouches[0];
    const deltaX = touch.clientX - this.touchStartX;
    const deltaY = Math.abs(touch.clientY - this.touchStartY);
    if (Math.abs(deltaX) > 60 && deltaY < 30) {
      this.replyToMessage = message;
    }
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
