# FreelanceHub — Project Documentation

## 1. Project Overview

**FreelanceHub** is a full-stack freelancing marketplace mobile application connecting **clients** who need services with **freelancers** who provide them. Built as a cross-platform mobile app, it features real-time messaging, a digital product store, project management with milestones, a recommendation engine, Stripe-powered payments, subscription plans, and a comprehensive admin dashboard.

---

## 2. Technology Stack

### 2.1 Frontend

| Technology | Version | Purpose |
|---|---|---|
| **Angular** | 20.x | Core SPA framework |
| **Ionic Framework** | 8.x | Mobile UI components & native feel |
| **Capacitor** | 8.3 | Native device APIs (haptics, keyboard, status bar, preferences) |
| **RxJS** | 7.8 | Reactive state & async management |
| **Socket.IO Client** | 4.8 | Real-time WebSocket communication |
| **TypeScript** | 5.9 | Type-safe development |
| **Ionicons** | 7.x | Icon library |
| **SCSS** | — | Component-scoped styling |

### 2.2 Backend

| Technology | Purpose |
|---|---|
| **Python / Flask** | REST API server |
| **Flask-PyMongo / PyMongo** | MongoDB ODM |
| **MongoDB** | NoSQL document database |
| **Flask-JWT-Extended** | JWT authentication (24h tokens) |
| **Flask-Bcrypt** | Password hashing |
| **Flask-SocketIO + Eventlet** | Real-time WebSocket server |
| **Flask-CORS** | Cross-origin resource sharing |
| **Stripe SDK** | Payment processing |
| **python-dotenv** | Environment variable management |

### 2.3 Infrastructure

- **Database**: MongoDB (configured via `MONGO_URI` env var)
- **File Storage**: Local filesystem (`backend/uploads/`)
- **Real-time**: Socket.IO over WebSocket with Eventlet
- **Auth**: JWT Bearer tokens, bcrypt password hashing
- **Payments**: Stripe (with mock fallback for dev)

---

## 3. Project Structure

```
mobile/
├── backend/
│   ├── app.py                  # Flask app factory, extensions, serializer
│   ├── config.py               # Config class (env vars, Stripe keys)
│   ├── decorators.py           # @jwt_optional, @role_required
│   ├── payment_config.py       # Commission rates, subscription plans, boost pricing
│   ├── payment_service.py      # Stripe integration helpers
│   ├── recommendation_engine.py # Scoring engine for offers & freelancers
│   ├── stats_helper.py         # Admin dashboard statistics
│   ├── email_templates.py      # HTML email templates
│   ├── seed.py                 # Database seeder with sample data
│   ├── create_indexes.py       # MongoDB index definitions
│   ├── requirements.txt        # Python dependencies
│   ├── .env                    # Environment variables
│   ├── uploads/                # User-uploaded files
│   └── routes/                 # API blueprints (26 route files)
│       ├── auth.py             # Registration, login, 2FA, password reset
│       ├── users.py            # Profile CRUD, privacy, account management
│       ├── offers.py           # Job offers, proposals, saved searches
│       ├── projects.py         # Milestones, tasks, deliverables, completion
│       ├── conversations.py    # Messaging with real-time delivery
│       ├── store.py            # Digital product marketplace
│       ├── payments.py         # Payment intents, transactions, wallet
│       ├── subscriptions.py    # Plan management, Stripe webhooks
│       ├── admin.py            # User/claim management, revenue analytics
│       ├── freelancer.py       # Freelancer dashboard stats
│       ├── client.py           # Client dashboard stats
│       ├── reviews.py          # User reviews
│       ├── follow.py           # Follow/unfollow system
│       ├── search.py           # Global search
│       ├── recommendations.py  # AI-powered recommendations
│       ├── time_tracking.py    # Timer start/stop/pause, reports
│       ├── analytics.py        # Platform analytics
│       ├── support.py          # Support ticket system
│       ├── notifications.py    # Push notifications
│       ├── earnings.py         # Freelancer earnings
│       ├── services.py         # Service listings
│       ├── proposals.py        # Proposal management
│       ├── freelancers.py      # Freelancer directory
│       ├── socket.py           # WebSocket event handlers
│       └── home.py             # Home feed
│
├── frontend/
│   └── src/app/
│       ├── app-routing.module.ts   # Route definitions with guards
│       ├── app.module.ts           # Root Angular module
│       ├── guards/                 # 6 route guards
│       │   ├── auth.guard.ts
│       │   ├── auth-required.guard.ts
│       │   ├── guest-allowed.guard.ts
│       │   ├── guest.guard.ts
│       │   ├── role.guard.ts
│       │   └── welcome.guard.ts
│       ├── interceptors/
│       │   └── auth.interceptor.ts # Auto-attaches JWT to requests
│       ├── models/                 # 10 TypeScript interfaces
│       ├── services/               # 22 Angular services
│       ├── components/             # 9 shared components
│       │   ├── auth-modal/
│       │   ├── guest-banner/
│       │   ├── freelancer-card/
│       │   ├── leave-review/
│       │   ├── portfolio-grid/
│       │   ├── add-portfolio-project-modal/
│       │   ├── interest-selector/
│       │   ├── quick-tour/
│       │   └── submit-proposal/
│       └── pages/                  # 22 page modules
│           ├── welcome-slides/
│           ├── role-selection/
│           ├── auth/
│           ├── onboarding/
│           ├── tabs/ (Home, Services, Offers, Messages, Profile)
│           ├── notifications/
│           ├── publish-offer/
│           ├── offer-proposals/
│           ├── admin-dashboard/
│           ├── client-dashboard/
│           ├── freelancer-dashboard/
│           ├── seller-dashboard/
│           ├── project-detail/
│           ├── profile/
│           ├── search/
│           ├── freelancer-search/
│           ├── digital-store/
│           ├── store/
│           ├── my-purchases/
│           ├── pricing/
│           └── services/
│
└── design_figma/                   # UI design assets
```

---

## 4. Core Features

### 4.1 Authentication & Authorization

- **Registration** with role selection (client / freelancer / admin)
- **Login** with email + password, JWT token (24h expiry)
- **Password Reset** via secure token (1h expiry)
- **Email Verification** via token (24h expiry)
- **Two-Factor Authentication (2FA)** using TOTP (pyotp)
- **Banned user detection** via JWT blocklist loader
- **Guest browsing** — unauthenticated users can browse offers, store, and freelancer profiles
- **Deferred authentication** — auth modal prompts login only when needed

**Route Guards** (frontend):
- `AuthGuard` — requires login
- `AuthRequiredGuard` — strict auth check with modal prompt
- `GuestAllowedGuard` — allows guest access
- `RoleGuard` — restricts by user role (client, freelancer, admin)
- `WelcomeGuard` — shows welcome slides on first visit

### 4.2 User Profiles

- **Freelancer profiles**: bio, title, hourly rate, skills, certifications, portfolio projects (with multi-image support), work experience, education, languages, video intro URL, CV upload
- **Profile completion tracker** — 10-point checklist with percentage and actionable suggestions
- **Availability status**: available / busy / unavailable
- **Online status** — computed from `last_login_at` (Online now / Response in 2h / Response today / Offline)
- **Badges**: "Top Rated" (≥4.8 rating, ≥5 reviews), "Fast Reply" (≥3 completed projects)
- **Shareable profile URL** via username slug (`/freelancer/:username`)
- **Follower system** with count display
- **Privacy settings**: show email/phone/location/earnings, message permissions, profile visibility

### 4.3 Account Management

- **Deactivate account** (soft delete, reactivatable within 30 days)
- **Reactivate account**
- **Delete account** (password-confirmed, anonymizes data, blocks if active projects exist)
- **Block/unblock users**

### 4.4 Job Offers & Proposals

**Clients** create offers with:
- Title, description, category, required skills
- Budget range (min/max), duration, location
- Status tracking (active/closed)

**Freelancers** submit proposals with:
- Cover letter, proposed price, estimated duration
- Recommendation context tracking (if recommended)

**Advanced Search**:
- Text search across title, description, skills
- Filters: category, location, duration, budget range, project type, experience level
- **Saved searches** with alert toggles

### 4.5 Project Management

Full lifecycle management once a freelancer is hired:

- **Milestones**: create, update status (pending → in_progress → done), set due dates, allocate budget
- **Tasks**: create under milestones, track status (todo → in_progress → review → done), assign priority (low/medium/high)
- **Deliverables**: upload file links per milestone, client confirmation workflow
- **Progress tracking**: auto-computed from tasks completion percentage
- **Budget management**: total budget, paid amount tracking
- **Project completion**: requires client rating (1-5) + review comment; creates a review record
- **Status transitions**: active → completed / cancelled / disputed (with reason)
- **Cross-project milestone view**: upcoming milestones across all active projects

### 4.6 Real-Time Messaging

- **Conversations**: one-to-one between participants, linked to offers
- **Messages**: text with reply-to support
- **Delivery receipts**: `delivered_to` array tracking
- **Read receipts**: `read_by` array + `is_read` flag
- **Typing indicators**: real-time via Socket.IO
- **Online presence**: user online/offline status broadcast to conversation rooms
- **Unread counts**: per-user per-conversation tracking

**Socket.IO Events**:
| Event | Direction | Description |
|---|---|---|
| `connect` | Client→Server | Authenticates via JWT, joins user + conversation rooms |
| `disconnect` | Client→Server | Broadcasts offline status |
| `message:new` | Server→Client | New message in conversation |
| `message:delivered` | Server→Client | Message delivery confirmation |
| `message:read` | Server→Client | Message read confirmation |
| `user:typing` | Bidirectional | Typing indicator toggle |
| `user:online` | Server→Client | Online/offline status change |
| `conversation:unread` | Server→Client | Unread count delta |

### 4.7 Digital Product Store

A marketplace for digital assets (templates, design files, code, documents):

- **Product listing** with filtering: category, search, file type, license, price range, tags, featured, sorting (recent/popular/price/rating)
- **5 main categories**: Website Templates, Mobile App Templates, Design Assets, Code Scripts, Business Documents
- **Product details**: preview images, demo URL, version, compatibility, what's included, license type (single/multiple/unlimited)
- **File management**: secure upload with SHA-256 checksum, file serving
- **Purchase system**: download token generation, download limit (5), download history with IP tracking
- **Product reviews**: rating (1-5) + comment, auto-computed average rating
- **Refunds**: 14-day eligibility window
- **Seller dashboard**: product management, sales analytics (monthly revenue, top products, recent sales), view/download/sales counters

### 4.8 Monetization System

#### Commission Structure
| Transaction Type | Fee | Applied To |
|---|---|---|
| Project | 15% (freelancer) + 3% (client) | Base rates |
| Store sale | 20% (seller) | Digital products |
| Service | 12% (provider) | Service listings |

*Subscribers receive reduced rates (Pro: 12%/17%, Business: 10%/15%)*

#### Subscription Plans
| Feature | Free | Professional ($19.99/mo) | Business ($49.99/mo) |
|---|---|---|---|
| Proposals/month | 10 | 50 | Unlimited |
| Offers/month | 3 | 15 | Unlimited |
| Commission rate | 15% | 12% | 10% |
| Store listings | 2 | 10 | Unlimited |
| Featured listing | ✗ | ✓ | ✓ |
| Priority support | ✗ | ✓ | ✓ |
| Analytics | Basic | Advanced | Premium |
| Verified badge | ✗ | ✓ | ✓ |
| Dedicated manager | ✗ | ✗ | ✓ |
| API access | ✗ | ✗ | ✓ |

#### Boost/Featured Listings
| Boost Type | Price | Duration |
|---|---|---|
| Offer Boost | $9.99 / $29.99 | 7 / 30 days |
| Service Feature | $7.99 | 7 days |
| Product Feature | $14.99 | 7 days |
| Profile Boost | $12.99 | 7 days |

#### Premium À La Carte Features
| Feature | Price | Duration |
|---|---|---|
| Urgent Badge | $4.99 | 3 days |
| Portfolio Video | $14.99 | 1 year |
| Advanced Analytics | $9.99 | 30 days |
| Proposal Templates | $2.99 | 1 year |

#### Wallet & Withdrawals
- Balance tracking (earned - withdrawn)
- Withdrawal methods: bank transfer, PayPal
- Standard withdrawal fee: $1.00
- Rush payout: $4.99 (instant vs 5-day)
- Currency conversion fee: 3%

### 4.9 Recommendation Engine

Multi-factor scoring algorithm with weighted components:

**For Clients (offer recommendations)**:
- Interest match (50%): NLP token matching against user interests
- Budget fit (20%): proximity to user's average budget
- Recency (20%): decay over 30 days
- Engagement (10%): inverse of proposal count (less competition = higher score)

**For Freelancers (opportunity matching)**:
- Skill match (50%): skills vs offer requirements
- Budget fit (20%): fixed at 0.6
- Recency (20%): same decay function
- Engagement (10%): same inverse competition score

**Interest category mapping**: Technology, Design, Content, Marketing, Video, Business — each with subcategories for fuzzy matching.

### 4.10 Time Tracking

- **Timer**: start, stop, pause, resume per project
- **Entries**: CRUD with project association, duration auto-calculation
- **Reports**: daily breakdown (grouped by project), summary report (configurable period)
- **Access control**: only the assigned freelancer can track; both client and freelancer can view

### 4.11 Support Ticket System

- **Create tickets** with subject, description, category, priority
- **Threaded replies** with internal notes support
- **Status workflow**: open → in_progress → resolved → closed
- **Priority levels**: low, normal, high, urgent
- **Ticket assignment** to support staff
- **Admin dashboard**: stats, filtering, search across all tickets

### 4.12 Admin Dashboard

- **User management**: list, search, filter by role/status, approve freelancers, ban/unban, delete
- **Claims management**: list, filter by status/priority/type, update status, add admin notes
- **Approval queue**: approve/reject offers and services with admin notes
- **Revenue analytics**: monthly revenue charts, revenue by type, subscription stats, MRR calculation, today's stats, pending withdrawals
- **Transaction browser**: filterable list of all platform transactions
- **Withdrawal processing**: approve/reject withdrawal requests

### 4.13 Notifications

- System notifications for: approvals, sales, payments, subscription changes, follows
- Read/unread tracking
- Seeded welcome notifications for new users

### 4.14 Follow System

- Follow/unfollow users
- Follower count on profiles
- Following status check for authenticated viewers

### 4.15 Search

- **Global search** across offers, freelancers, and services
- **Freelancer search** with skill and category filters
- **Offer search** with multi-criteria filtering

---

## 5. API Reference

Base URL: `http://localhost:5000/api`

### Authentication
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/auth/register` | — | Register new user |
| POST | `/auth/login` | — | Login |
| GET | `/auth/me` | JWT | Get current user |
| POST | `/auth/forgot-password` | — | Request password reset |
| POST | `/auth/reset-password` | — | Reset password with token |
| POST | `/auth/send-verification-email` | JWT | Send verification email |
| POST | `/auth/verify-email` | — | Verify email with token |
| POST | `/auth/2fa/setup` | JWT | Generate 2FA secret |
| POST | `/auth/2fa/verify` | JWT | Verify and enable 2FA |
| POST | `/auth/2fa/disable` | JWT | Disable 2FA |

### Users & Profiles
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/users/profile` | JWT | Own profile |
| PUT | `/users/profile` | JWT | Update profile |
| GET | `/users/:id/profile` | — | Public profile |
| GET | `/users/freelancer/:username` | — | Profile by username |
| PUT | `/users/onboarding` | JWT | Update onboarding prefs |
| PUT | `/users/interests` | JWT | Update interests |
| POST | `/users/profile/cv` | JWT | Upload CV |
| POST | `/users/deactivate` | JWT | Deactivate account |
| POST | `/users/reactivate` | JWT | Reactivate account |
| DELETE | `/users/delete` | JWT | Delete account |
| GET/PUT | `/users/privacy-settings` | JWT | Privacy settings |
| POST | `/users/block-user/:id` | JWT | Block user |
| POST | `/users/unblock-user/:id` | JWT | Unblock user |

### Offers & Proposals
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/offers/` | — | List active offers |
| GET | `/offers/mine` | JWT | My offers (client) |
| GET | `/offers/:id` | — | Offer detail |
| POST | `/offers/` | JWT(client) | Create offer |
| GET | `/offers/search` | — | Advanced search |
| POST | `/offers/:id/proposals` | JWT(freelancer) | Submit proposal |
| GET | `/offers/:id/proposals` | JWT(client) | View proposals |
| POST/GET/DELETE | `/offers/saved-searches` | JWT | Saved searches |

### Projects
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/projects/:id/detail` | JWT | Full project detail |
| GET | `/projects/:id/progress` | JWT | Progress overview |
| POST | `/projects/:id/milestones` | JWT(client) | Create milestone |
| PATCH | `/projects/:id/milestones/:mid` | JWT(client) | Update milestone |
| POST | `/projects/:id/tasks` | JWT(client) | Create task |
| PATCH | `/projects/:id/tasks/:tid` | JWT(client) | Update task |
| DELETE | `/projects/:id/tasks/:tid` | JWT(client) | Delete task |
| POST/GET | `/projects/:id/deliverables` | JWT | Manage deliverables |
| PATCH | `/projects/:id/budget` | JWT(client) | Update budget |
| PATCH | `/projects/:id/complete` | JWT(client) | Complete project |
| PATCH | `/projects/:id/status` | JWT(client) | Cancel/dispute |
| GET | `/projects/upcoming-milestones` | JWT | Cross-project milestones |

### Messaging
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/conversations/` | JWT | List conversations |
| POST | `/conversations/` | JWT | Create conversation |
| GET | `/conversations/:id/messages` | JWT | Get messages (paginated) |
| POST | `/conversations/:id/messages` | JWT | Send message |
| POST | `/conversations/:id/read` | JWT | Mark as read |

### Digital Store
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/store/products` | — | Browse products |
| GET | `/store/products/featured` | — | Featured products |
| GET | `/store/products/categories` | — | Category list |
| GET | `/store/products/:id` | — | Product detail |
| POST | `/store/products` | JWT(freelancer) | Create product |
| PUT | `/store/products/:id` | JWT(owner) | Update product |
| DELETE | `/store/products/:id` | JWT(owner) | Delete product |
| POST | `/store/products/:id/purchase` | JWT | Purchase product |
| GET | `/store/purchases` | JWT | My purchases |
| GET | `/store/purchases/:id/download` | JWT | Download purchased file |
| GET/POST | `/store/products/:id/reviews` | —/JWT | Product reviews |
| POST | `/store/purchases/:id/refund` | JWT | Request refund |
| GET | `/store/seller/products` | JWT | Seller's products |
| GET | `/store/seller/analytics` | JWT | Seller analytics |

### Payments & Subscriptions
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/payments/create-intent` | JWT | Create payment intent |
| POST | `/payments/confirm` | JWT | Confirm payment |
| GET | `/payments/transactions` | JWT | Transaction history |
| POST | `/payments/calculate` | — | Fee calculator |
| POST | `/payments/boost` | JWT | Purchase boost |
| GET | `/payments/boost/options` | — | Boost options |
| POST/GET | `/payments/premium/*` | JWT | Premium features |
| GET | `/payments/wallet` | JWT | Wallet balance |
| POST | `/payments/withdraw` | JWT | Request withdrawal |
| GET | `/subscriptions/plans` | — | List plans |
| GET | `/subscriptions/current` | JWT | Current subscription |
| POST | `/subscriptions/subscribe` | JWT | Subscribe |
| POST | `/subscriptions/cancel` | JWT | Cancel subscription |
| POST | `/subscriptions/change-plan` | JWT | Change plan |
| POST | `/subscriptions/check-feature` | JWT | Check feature access |

### Time Tracking
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/time-tracking/start` | JWT | Start timer |
| POST | `/time-tracking/stop/:id` | JWT | Stop timer |
| POST | `/time-tracking/pause/:id` | JWT | Pause timer |
| POST | `/time-tracking/resume/:id` | JWT | Resume timer |
| GET | `/time-tracking/entries/:project_id` | JWT | Project entries |
| GET | `/time-tracking/entries` | JWT | My entries |
| GET | `/time-tracking/report/daily` | JWT | Daily report |
| GET | `/time-tracking/report/summary` | JWT | Summary report |

### Admin
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/admin/stats` | Admin | Dashboard stats |
| GET | `/admin/users` | Admin | User management |
| PATCH | `/admin/users/:id/ban` | Admin | Ban user |
| PATCH | `/admin/users/:id/approve` | Admin | Approve freelancer |
| GET | `/admin/claims` | Admin | Claims list |
| GET | `/admin/revenue/stats` | Admin | Revenue analytics |
| GET | `/admin/revenue/transactions` | Admin | All transactions |
| GET/PATCH | `/admin/revenue/withdrawals` | Admin | Process withdrawals |

### Support
| Method | Endpoint | Auth | Description |
|---|---|---|---|
| POST | `/support/tickets` | JWT | Create ticket |
| GET | `/support/tickets` | JWT | My tickets |
| POST | `/support/tickets/:id/reply` | JWT | Reply to ticket |
| PUT | `/support/tickets/:id/status` | Admin | Update status |
| GET | `/support/admin/stats` | Admin | Support stats |

---

## 6. Database Collections

| Collection | Description |
|---|---|
| `users` | User accounts (all roles) |
| `freelancer_profiles` | Extended freelancer profile data |
| `offers` | Client job postings |
| `proposals` | Freelancer proposals for offers |
| `projects` | Active/completed projects (embeds milestones, tasks, deliverables) |
| `conversations` | Chat conversations between users |
| `messages` | Individual chat messages |
| `store_products` | Digital marketplace products |
| `store_purchases` | Purchase records with download tokens |
| `product_reviews` | Reviews for store products |
| `reviews` | User-to-user reviews (project completion) |
| `transactions` | Financial transaction records |
| `subscriptions` | Active subscription records |
| `boost_purchases` | Boost/featured listing purchases |
| `user_premium_features` | À la carte premium feature grants |
| `withdrawals` | Withdrawal requests |
| `notifications` | User notifications |
| `follows` | Follow relationships |
| `claims` | Dispute claims |
| `user_bans` | Ban history |
| `support_tickets` | Support ticket threads |
| `time_entries` | Time tracking entries |
| `saved_searches` | Saved offer search filters |
| `password_resets` | Password reset tokens |
| `email_verifications` | Email verification tokens |
| `approval_requests` | Content approval queue |
| `account_actions` | Account lifecycle audit log |
| `recommendation_interactions` | Recommendation tracking |

---

## 7. Application Workflow

### 7.1 User Onboarding Flow

```
Welcome Slides → Role Selection (Client/Freelancer)
     → Registration (name, email, password, interests)
         → Onboarding Preferences
             → Main App (Tabs: Home/Services/Offers/Messages/Profile)
```

Guest users can browse the app freely; authentication is prompted only when performing protected actions (submitting proposals, messaging, purchasing).

### 7.2 Client Workflow

1. **Post an Offer** — define requirements, budget, skills needed
2. **Review Proposals** — see freelancer proposals with cover letters and pricing
3. **Hire & Create Project** — assign freelancer, set budget
4. **Manage Project** — create milestones, tasks; track progress
5. **Review Deliverables** — confirm deliverables per milestone
6. **Complete & Review** — mark project complete with rating + review
7. **Pay** — Stripe payment with commission breakdown

### 7.3 Freelancer Workflow

1. **Complete Profile** — fill bio, skills, portfolio, certifications
2. **Browse Offers** — search/filter opportunities, view recommendations
3. **Submit Proposals** — cover letter, proposed price, estimated duration
4. **Work on Projects** — track time, upload deliverables
5. **Sell Digital Products** — list items in the store, manage sales
6. **Earn & Withdraw** — track earnings in wallet, request withdrawals

### 7.4 Payment Flow

```
Client initiates payment
  → POST /payments/create-intent (calculates commission, creates Stripe PaymentIntent)
  → Client confirms on frontend (Stripe Elements)
  → POST /payments/confirm (verifies with Stripe, records transaction)
  → Seller receives notification
  → Net amount added to seller's wallet
  → Seller requests withdrawal → Admin approves → Payout
```

### 7.5 Real-Time Messaging Flow

```
User connects with JWT → Socket.IO authenticates
  → Joins user room + all conversation rooms
  → Online status broadcast to conversation participants
  → Send message via REST POST
  → Server emits message:new to conversation room
  → Recipients receive, delivery receipts sent
  → User opens conversation → marks as read → read receipts sent
```

---

## 8. Security Measures

- **Password hashing**: bcrypt with salt
- **JWT tokens**: 24-hour expiry, secret key via env var
- **Token blocklist**: banned users checked on every request
- **CORS**: configured for API routes
- **Input validation**: server-side validation on all endpoints
- **File upload**: extension whitelist, secure filename sanitization, size limit (50MB)
- **File integrity**: SHA-256 checksums for store products
- **Download protection**: token-based downloads with per-purchase limits
- **Account deletion**: data anonymization instead of hard delete
- **Password reset**: secure random tokens with 1-hour expiry
- **2FA**: TOTP-based with pyotp
- **Role-based access**: decorators and guards enforce permissions
- **Privacy settings**: granular control over profile visibility

---

## 9. Setup & Running

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Create .env file with:
# MONGO_URI=mongodb://localhost:27017/freelancehub
# SECRET_KEY=your-secret
# JWT_SECRET_KEY=your-jwt-secret
# STRIPE_SECRET_KEY=sk_test_...
# STRIPE_PUBLISHABLE_KEY=pk_test_...

python seed.py                  # Seed sample data
python app.py                   # Start server on port 5000
```

### Frontend

```bash
cd frontend
npm install
npm start                       # Start dev server on port 4200
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB connection string |
| `SECRET_KEY` | Yes | Flask secret key |
| `JWT_SECRET_KEY` | Yes | JWT signing key |
| `STRIPE_SECRET_KEY` | No | Stripe secret key (mock mode if absent) |
| `STRIPE_PUBLISHABLE_KEY` | No | Stripe publishable key |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook signing secret |
| `FRONTEND_URL` | No | Frontend URL for email links (default: localhost:4200) |

---

## 10. Key Design Decisions

1. **MongoDB over SQL** — document model fits the varied, nested data (projects embed milestones/tasks/deliverables) and allows flexible schema evolution
2. **Flask Blueprints** — 26 modular route files keep the codebase organized and maintainable
3. **Lazy-loaded Angular modules** — each page is a separate module loaded on demand for performance
4. **Guest-first UX** — users can explore the full marketplace before being prompted to authenticate
5. **Socket.IO for real-time** — provides WebSocket transport with fallback, room-based messaging, and typing/presence indicators
6. **Stripe with mock fallback** — production-ready payment integration that degrades gracefully in development
7. **Multi-factor scoring** — recommendation engine uses weighted composite scores rather than simple filtering for better relevance
8. **Soft deletes** — products and accounts use soft delete flags for data integrity and auditability
