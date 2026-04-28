# FreelanceHub Mobile Application - Project Documentation

## 1. Project Overview
FreelanceHub is a modern, mobile-first freelance marketplace designed to connect clients with talented freelancers. It supports role-based access control (Admin, Client, Freelancer), enabling clients to publish offers, freelancers to submit proposals, and both parties to interact through a unified, responsive interface.

---

## 2. Technology Stack

### Frontend (Mobile & Web)
- **Framework**: Angular
- **UI Toolkit**: Ionic Framework (Ionic 6+)
- **State Management**: RxJS & Angular Services
- **Routing**: Angular Router with Navigation Guards

### Backend (API)
- **Framework**: Flask (Python)
- **Database**: SQLite (via `models.py`)
- **Authentication**: JWT (JSON Web Tokens)

---

## 3. Project Structure

The repository is divided into two distinct environments:

### `backend/`
Contains the Flask API, database models, and routes.
- **`app.py` / `routes/`**: Main entry point and REST API endpoints.
- **`models.py`**: SQLAlchemy database schemas (User, Offer, Proposal, Review, Notification).
- **`config.py`**: Application configuration (JWT secrets, DB URIs).

### `frontend/`
Contains the Ionic Angular application.
- **`src/app/pages/`**: Main application views (Home, Store, Offer Proposals, Notifications, Profiles, Auth).
- **`src/app/services/`**: API integration, HTTP requests, and state management (`AuthService`, `OfferService`, `ProposalService`).
- **`src/app/models/`**: TypeScript interfaces corresponding to backend models (`review.model.ts`, `proposal.model.ts`, etc.).
- **`src/app/guards/`**: Role-based route protection to ensure clients and freelancers stay in their designated flows.
- **`src/app/interceptors/`**: HTTP Interceptors to automatically attach JWT tokens to secure requests.

---

## 4. Core Features & Implementation Strategies

### 4.1 Authentication & Role-Based Access Control (RBAC)
- **Description**: Users register and log in as either a Client or a Freelancer. The app dynamically adapts the UI depending on the role.
- **Implementation**:
  - **Backend**: `/login` and `/register` endpoints authenticate credentials and return a JWT with the user's role embedded in the payload.
  - **Frontend**: The `AuthService` stores the token locally and parses the user role. Angular `CanActivate` guards prevent unauthorized access to specific pages (e.g., only Clients can publish an offer).

### 4.2 Job Marketplace (Store)
- **Description**: A central hub where freelancers can browse job offers and clients can view platform statistics.
- **Implementation**:
  - **Frontend**: `StorePage` fetches a paginated list of offers via the `OfferService`. Includes a reactive search bar with debounce functionality, skeleton loaders for fetching states, and pull-to-refresh (`ion-refresher`) functionality.
  - **Backend**: Filtering endpoints allow querying active offers by search term, location type (Remote, Hybrid), or category.

### 4.3 Proposal System
- **Description**: Freelancers can submit proposals to job offers, defining their cover letter and expected budget. Clients can review, accept, or reject these proposals.
- **Implementation**:
  - **Freelancer Flow**: Calling `applyForOffer()` opens a modal to input proposal details. `ProposalService.submitProposal()` sends the data to the API.
  - **Client Flow**: Clients view their offers' proposals via `OfferProposalsPage`, where they use `updateProposal(id, status)` to accept/reject candidates. Success UI toasts are displayed upon confirmation.
  - **Backend**: `POST /offers/<id>/proposals` creates a proposal. `PATCH /proposals/<id>` updates the status.

### 4.4 Notifications
- **Description**: Alerts for proposal updates, system messages, or application status changes.
- **Implementation**:
  - **Frontend**: A dedicated `NotificationsPage` retrieves data via `NotificationService`. Features include marking notifications as read, deleting them, and displaying unread badges on the navigation bar.
  - **Backend**: Automatically triggers notification generation during key events (e.g., when a Client accepts a proposal, a notification record is inserted into the database for the assigned Freelancer).

### 4.5 User Profiles & Reviews
- **Description**: Detailed profile pages for freelancers showing their skills, and for clients showing their reputation.
- **Implementation**:
  - **Frontend**: Leveraging the `Review` model (which links `reviewer_id` and `target_user_id`). Clients can leave reviews with a 1-5 rating and comment after a job is completed.
  - **Backend**: Relational mapping between Users and Reviews in `models.py`.

---

## 5. Deployment & Running Locally

### Backend Setup
1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create and activate a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```bash
   python app.py
   ```

### Frontend Setup
1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install NPM dependencies:
   ```bash
   npm install
   ```
3. Start the Ionic development server:
   ```bash
   ionic serve
   ```
The app should automatically open in your default browser at `http://localhost:8100`.
