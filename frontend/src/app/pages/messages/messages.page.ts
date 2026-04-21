import { Component, OnInit, OnDestroy, ViewChild, ElementRef } from '@angular/core';
import { ConversationService } from '../../services/conversation.service';
import { AuthService } from '../../services/auth.service';
import { Conversation, Message } from '../../models/conversation.model';
import { User } from '../../models/user.model';
import { Subscription } from 'rxjs';

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

  private pollInterval: any;
  private subs: Subscription[] = [];
  private searchTimeout: any;

  constructor(
    private conversationService: ConversationService,
    private authService: AuthService
  ) {}

  ngOnInit() {
    this.subs.push(
      this.authService.currentUser$.subscribe(user => {
        this.currentUser = user;
        if (user) {
          this.loadConversations();
        }
      })
    );
  }

  ngOnDestroy() {
    this.subs.forEach(s => s.unsubscribe());
    this.stopPolling();
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
    this.startPolling();
    
    // Optimistically clear unread count locally
    conv.unread_count = 0;
    const totalUnread = this.conversations.reduce((acc, curr) => acc + curr.unread_count, 0);
    this.conversationService.updateUnreadCount(totalUnread);
  }

  backToList() {
    this.isMobileRightPanelOpen = false;
    this.selectedConversation = null;
    this.stopPolling();
    this.loadConversations(); // refresh counts
  }

  loadMessages() {
    if (!this.selectedConversation) return;
    
    this.isLoadingMessages = true;
    this.conversationService.getMessages(this.selectedConversation.id, 1, 100).subscribe({
      next: (res) => {
        this.messages = res.messages;
        this.isLoadingMessages = false;
        this.scrollToBottom();
      },
      error: () => {
        this.isLoadingMessages = false;
      }
    });
  }

  startPolling() {
    this.stopPolling();
    this.pollInterval = setInterval(() => {
      if (this.selectedConversation) {
        this.conversationService.getMessages(this.selectedConversation.id, 1, 100).subscribe(res => {
          // Only update if there are new messages
          if (res.messages.length > this.messages.length) {
             this.messages = res.messages;
             this.scrollToBottom();
             // Refetch conversations to update last message locally
             this.conversationService.getConversations().subscribe(cRes => {
                this.conversations = cRes.conversations;
             });
          }
        });
      }
    }, 3000);
  }

  stopPolling() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
  }

  sendMessage() {
    if (!this.newMessageContent.trim() || !this.selectedConversation || this.isSending) return;

    this.isSending = true;
    const content = this.newMessageContent.trim();
    this.newMessageContent = '';

    this.conversationService.sendMessage(this.selectedConversation.id, content).subscribe({
      next: (res) => {
        this.messages.push(res.message);
        this.isSending = false;
        this.scrollToBottom();
        this.selectedConversation!.last_message = content;
        this.selectedConversation!.last_message_at = res.message.created_at;
      },
      error: () => {
        this.isSending = false;
        this.newMessageContent = content; // restore on fail
      }
    });
  }

  onKeydown(event: KeyboardEvent) {
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
}
