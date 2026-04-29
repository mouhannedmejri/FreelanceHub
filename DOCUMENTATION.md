# FreelanceHub Mobile Application Documentation

## 1. Project Overview

FreelanceHub is a role-based freelance marketplace built as an Ionic + Angular client application backed by a Flask REST API. The platform supports three roles:

- `client`: publishes project offers, reviews proposals, and manages project progress.
- `freelancer`: browses offers/services, sends proposals, manages conversations, and tracks work and earnings.
- `admin`: moderates users, approvals, and claims; monitors platform-level metrics.

The application is designed around a mobile-first experience (Ionic UI), with API-driven state and JWT authentication.

---

## 2. Technology Stack

### Frontend

- Angular (standalone module architecture with lazy-loaded routes)
- Ionic Framework UI components
- Capacitor (mobile runtime integrations)
- RxJS + Angular services for API/data flow
- Route guards (`AuthGuard`, `RoleGuard`)
- HTTP interceptor for JWT injection

### Backend

- Flask application factory (`create_app()`)
- Flask-PyMongo (MongoDB access)
- Flask-JWT-Extended (token auth)
- Flask-Bcrypt (password hashing)
- Flask-CORS
- python-dotenv for environment variables

### Data Layer

- MongoDB collections (document model)
- Explicit object serialization helpers in backend (`serialize`, `serialize_list`)

---

## 3) High-Level Architecture

## 3.1 Repository Layout

- `backend/` - Flask API, route blueprints, config, helper services, seed script.
- `frontend/` - Ionic Angular app (pages, services, guards, interceptor, styling).
- `design_figma/` - visual design references/screenshots.

## 3.2 Backend Composition

- Entry point and app setup: `backend/app.py`
- Configuration: `backend/config.py`
- Feature routes: `backend/routes/*.py`
- Aggregation utilities: `backend/stats_helper.py`
- Database seeding: `backend/seed.py`

`app.py` creates the Flask app, initializes extensions, registers blueprints, and defines JWT checks (including blocked/banned user validation).

## 3.3 Frontend Composition

- Root module and providers: `frontend/src/app/app.module.ts`
- Application routing: `frontend/src/app/app-routing.module.ts`
- Tabs shell routing: `frontend/src/app/pages/tabs/tabs-routing.module.ts`
- Feature pages: `frontend/src/app/pages/**`
- API services: `frontend/src/app/services/**`
- Auth interceptor: `frontend/src/app/interceptors/auth.interceptor.ts`

---

## 4) User Roles and Permissions

## 4.1 Client

- Can create offers
- Can view proposals for owned offers
- Can accept/reject proposals
- Can access client dashboard and project tracking
- Can message freelancers and receive notifications

## 4.2 Freelancer

- Can browse offers/services/store
- Can submit proposals to offers
- Can manage profile and upload CV
- Can access freelancer dashboard, earnings, and reviews
- Can communicate through conversations/messages

## 4.3 Admin

- Can view global stats and moderation queues
- Can approve/reject requests (offers/services)
- Can ban/unban/delete users
- Can review and resolve claims/disputes

Role checks are enforced in both layers:

- frontend route guards (`RoleGuard`) for UX-level protection.
- backend decorators/guards (`admin_required`, `client_required`, `freelancer_required`) for server-side enforcement.

---

## 5) Core Features (Functional Documentation)

## 5.1 Authentication and Session Management

### Frontend Behavior

- User registers or logs in from the auth page.
- Token and user context are persisted (Preferences/local client storage pattern).
- JWT is automatically attached to API calls by `AuthInterceptor`.
- Access to restricted pages is controlled through guards and role metadata.

### Backend Behavior

- `POST /api/auth/register` creates users with role validation.
- `POST /api/auth/login` authenticates credentials and returns JWT.
- `GET /api/auth/me` returns current user profile context.
- JWT callback checks blocked/banned users before allowing token usage.

## 5.2 Offer Marketplace (Client Posts, Freelancer Browses)

- Clients create offers through publish flow.
- Freelancers browse offers and inspect details.
- Clients retrieve their own offers separately.

Relevant backend endpoints (`/api/offers`):

- list offers
- get single offer
- create offer
- list my offers

## 5.3 Proposal Lifecycle

- Freelancers submit proposals against specific offers.
- Clients list proposals per offer.
- Clients accept/reject proposals.

Relevant endpoints:

- `POST /api/offers/<offer_id>/proposals`
- `GET /api/offers/<offer_id>/proposals`
- `PATCH /api/proposals/<proposal_id>`

This lifecycle feeds notification generation and dashboard metrics.

## 5.4 Services and Digital Store

The platform has two parallel catalog systems:

- `services` marketplace (`/api/services`): freelancer service offerings.
- digital products store (`/api/store`): downloadable/sellable products.

Freelancers can create products/services; other users can browse catalog entries.

## 5.5 Messaging and Conversations

- Users can create conversations directly or from offer context.
- Message threads support participant-based communication and unread tracking.

Endpoints (`/api/conversations`):

- list conversations
- create conversation
- list messages in conversation
- send message

## 5.6 Notifications

Dedicated notification center supports:

- listing notifications
- marking single notification as read
- marking all as read
- deleting notifications

The backend emits notification records during key business events (proposal updates, moderation changes, etc.).

## 5.7 Reviews and Reputation

- Users can create reviews for other users after project collaboration.
- Public profile views include reviews and rating context.

Endpoints:

- `POST /api/reviews`
- `GET /api/users/<id>/reviews`

## 5.8 Role-Specific Dashboards and Statistics

Dedicated route groups expose scoped analytics:

- `/api/client` - dashboard and project views for clients.
- `/api/freelancer` - dashboard, projects, earnings, and review stats.
- `/api/admin` - moderation tools and global management.
- `/api/home` - general home statistics.

`backend/stats_helper.py` centralizes aggregation logic for admin/client/freelancer metrics.

---

## 6) API Route Inventory

All routes are Flask blueprints registered in `backend/app.py`.

- `backend/routes/auth.py` -> `/api/auth`
- `backend/routes/home.py` -> `/api/home`
- `backend/routes/users.py` -> `/api/users`
- `backend/routes/offers.py` -> `/api/offers`
- `backend/routes/proposals.py` -> `/api/proposals`
- `backend/routes/services.py` -> `/api/services`
- `backend/routes/store.py` -> `/api/store`
- `backend/routes/conversations.py` -> `/api/conversations`
- `backend/routes/notifications.py` -> `/api/notifications`
- `backend/routes/reviews.py` -> `/api/reviews` (+ user review retrieval routes)
- `backend/routes/client.py` -> `/api/client`
- `backend/routes/freelancer.py` -> `/api/freelancer`
- `backend/routes/admin.py` -> `/api/admin`

---

## 7) Data Model (Conceptual)

Main collections/entities inferred from `seed.py` and route usage:

- `users`
- `freelancer_profiles`
- `offers`
- `proposals`
- `projects`
- `services`
- `store_products`
- `conversations`
- `messages`
- `notifications`
- `reviews`
- `approval_requests`
- `claims`
- `user_bans`

Key relationships:

- client `users` create many `offers`.
- offer has many `proposals` from freelancers.
- accepted proposal typically maps to `projects`.
- `conversations` contain many `messages`.
- `reviews` map reviewer -> target user.
- moderation entities (`approval_requests`, `claims`, `user_bans`) support admin workflows.

---

## 8) Frontend UX and Design Language

## 8.1 Design Principles

- Mobile-first layout through Ionic components.
- Fast navigability through tabs + side menu shell.
- Role-adaptive UI: visible actions and destinations vary by role.

## 8.2 Visual System

- Dark-first theme with custom Ionic CSS variables.
- Purple/violet primary branding palette.
- Frequent use of gradients, rounded cards, and elevated surfaces.
- Consistent icon-led cards and badge chips for status indicators.

Core style files:

- `frontend/src/theme/variables.scss` (design tokens, theme variables)
- `frontend/src/global.scss` (global defaults and app-wide styles)
- page-level SCSS files for local visual treatment

## 8.3 Navigation Design

- Main shell via tabs (`dashboard`, `services`, `messages`, `store`, `digital-store`, `profile`)
- Role-protected standalone pages:
  - `admin-dashboard`
  - `client-dashboard`
  - `freelancer-dashboard`
  - `publish-offer`
  - `offer-proposals/:id`

This architecture keeps core browsing actions always accessible while isolating role-exclusive workflows.

---

## 9) Local Development Setup

## 9.1 Backend

```bash
cd backend
python -m venv venv
# Windows PowerShell:
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Backend default URL: `http://localhost:5000`

## 9.2 Frontend

```bash
cd frontend
npm install
ionic serve
```

Frontend default URL: `http://localhost:8100`

API base URL is configured in:

- `frontend/src/environments/environment.ts`

---

## 10) Seed Data and Testing Notes

- `backend/seed.py` provides representative users, offers, proposals, projects, products, conversations, and moderation data.
- Seeded datasets are useful for:
  - dashboard visualization testing
  - role-based flow verification
  - moderation and claim lifecycle testing

---

## 11) Suggested Future Documentation Additions

- OpenAPI/Swagger spec for each endpoint contract.
- Sequence diagrams for key workflows (offer -> proposal -> project -> review).
- Permissions matrix (endpoint x role x action).
- Deployment guide for production (env vars, CORS policy, security hardening, backup/restore).
