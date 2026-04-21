from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import enum

db = SQLAlchemy()
bcrypt = Bcrypt()


class RoleEnum(enum.Enum):
    freelancer = 'freelancer'
    client = 'client'
    admin = 'admin'


class NotificationTypeEnum(enum.Enum):
    message = 'message'
    offer = 'offer'
    payment = 'payment'
    review = 'review'


class CategoryEnum(enum.Enum):
    developpement = 'Développement'
    design = 'Design'
    marketing = 'Marketing'
    redaction = 'Rédaction'


class LevelEnum(enum.Enum):
    junior = 'Junior'
    senior = 'Senior'
    expert = 'Expert'


class OfferStatusEnum(enum.Enum):
    active = 'active'
    closed = 'closed'


class LocationEnum(enum.Enum):
    remote = 'Remote'
    hybrid = 'Hybrid'
    onsite = 'Onsite'

class ProductCategoryEnum(enum.Enum):
    starter_kit = 'starter-kit'
    ui_kit = 'ui-kit'
    template = 'template'
    plan_archi = 'plan-archi'

class ProposalStatusEnum(enum.Enum):
    pending = 'pending'
    accepted = 'accepted'
    rejected = 'rejected'


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.client)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    is_approved = db.Column(db.Boolean, default=True)

    notifications = db.relationship('Notification', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    services = db.relationship('Service', backref='freelancer', lazy='dynamic')
    offers = db.relationship('Offer', backref='client', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_approved': self.is_approved,
        }


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type = db.Column(db.Enum(NotificationTypeEnum), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type.value,
            'title': self.title,
            'body': self.body,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class FreelancerProfile(db.Model):
    __tablename__ = 'freelancer_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    bio = db.Column(db.Text, default='')
    title = db.Column(db.String(200), default='')
    hourly_rate = db.Column(db.Float, default=0)
    location = db.Column(db.String(100), default='')
    phone = db.Column(db.String(20), default='')
    skills = db.Column(db.JSON, default=list)
    cv_filename = db.Column(db.String(255), default='')
    cv_size = db.Column(db.Integer, default=0)

    user = db.relationship('User', backref=db.backref('profile', uselist=False))
    certifications = db.relationship('Certification', primaryjoin="FreelancerProfile.user_id == Certification.user_id", foreign_keys="Certification.user_id", backref='freelancer_profile', lazy='dynamic', cascade='all, delete-orphan')
    portfolio_items = db.relationship('PortfolioItem', primaryjoin="FreelancerProfile.user_id == PortfolioItem.user_id", foreign_keys="PortfolioItem.user_id", backref='freelancer_profile', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'bio': self.bio or '',
            'title': self.title or '',
            'hourly_rate': self.hourly_rate or 0,
            'location': self.location or '',
            'phone': self.phone or '',
            'skills': self.skills or [],
            'certifications': [c.to_dict() for c in self.certifications],
            'portfolio': [p.to_dict() for p in self.portfolio_items],
            'cv_filename': self.cv_filename or '',
            'cv_size': self.cv_size or 0,
        }

class Certification(db.Model):
    __tablename__ = 'certifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    issuer = db.Column(db.String(200), nullable=False)
    year = db.Column(db.String(10), nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'issuer': self.issuer,
            'year': self.year,
        }

class PortfolioItem(db.Model):
    __tablename__ = 'portfolio_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default='')
    skills = db.Column(db.JSON, default=list)
    image_url = db.Column(db.String(500), default='')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'skills': self.skills or [],
            'image_url': self.image_url,
        }


class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(CategoryEnum), nullable=False)
    cover_image_url = db.Column(db.String(500), default='')
    tags = db.Column(db.JSON, default=list)
    level = db.Column(db.Enum(LevelEnum), nullable=False)
    price_from = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'freelancer_id': self.freelancer_id,
            'freelancer_name': self.freelancer.full_name if self.freelancer else '',
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'cover_image_url': self.cover_image_url or '',
            'tags': self.tags or [],
            'level': self.level.value,
            'price_from': self.price_from,
            'rating': self.rating or 0,
            'review_count': self.review_count or 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Offer(db.Model):
    __tablename__ = 'offers'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(CategoryEnum), nullable=False)
    skills = db.Column(db.JSON, default=list)
    budget_min = db.Column(db.Float, nullable=False, default=0)
    budget_max = db.Column(db.Float, nullable=False, default=0)
    duration = db.Column(db.String(50), default='')
    location = db.Column(db.Enum(LocationEnum), nullable=False, default=LocationEnum.remote)
    proposals_count = db.Column(db.Integer, default=0)
    status = db.Column(db.Enum(OfferStatusEnum), nullable=False, default=OfferStatusEnum.active)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'client_name': self.client.full_name if self.client else '',
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'skills': self.skills or [],
            'budget_min': self.budget_min,
            'budget_max': self.budget_max,
            'duration': self.duration or '',
            'location': self.location.value,
            'proposals_count': self.proposals_count,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Conversation(db.Model):
    __tablename__ = 'conversations'

    id = db.Column(db.Integer, primary_key=True)
    participant_1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    participant_2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=True)
    last_message = db.Column(db.Text, default='')
    last_message_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    unread_count_p1 = db.Column(db.Integer, default=0)
    unread_count_p2 = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    participant_1 = db.relationship('User', foreign_keys=[participant_1_id])
    participant_2 = db.relationship('User', foreign_keys=[participant_2_id])
    offer = db.relationship('Offer', foreign_keys=[offer_id])
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'participant_1_id': self.participant_1_id,
            'participant_2_id': self.participant_2_id,
            'offer_id': self.offer_id,
            'last_message': self.last_message,
            'last_message_at': self.last_message_at.isoformat() if self.last_message_at else None,
            'unread_count_p1': self.unread_count_p1,
            'unread_count_p2': self.unread_count_p2,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'participant_1': self.participant_1.to_dict() if self.participant_1 else None,
            'participant_2': self.participant_2.to_dict() if self.participant_2 else None,
            'offer': self.offer.to_dict() if self.offer else None,
        }

class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    sender = db.relationship('User', foreign_keys=[sender_id])

    def to_dict(self):
        return {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'content': self.content,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.Enum(ProductCategoryEnum), nullable=False)
    skills = db.Column(db.JSON, default=list)
    price = db.Column(db.Float, nullable=False)
    rating = db.Column(db.Float, default=0.0)
    sales_count = db.Column(db.Integer, default=0)
    version = db.Column(db.String(50), default='1.0.0')
    image_url = db.Column(db.String(500), default='')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    seller = db.relationship('User', foreign_keys=[seller_id])

    def to_dict(self):
        return {
            'id': self.id,
            'seller_id': self.seller_id,
            'title': self.title,
            'description': self.description,
            'category': self.category.value,
            'skills': self.skills or [],
            'price': self.price,
            'rating': self.rating,
            'sales_count': self.sales_count,
            'version': self.version,
            'image_url': self.image_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'seller_name': self.seller.full_name if self.seller else ''
        }

class Proposal(db.Model):
    __tablename__ = 'proposals'

    id = db.Column(db.Integer, primary_key=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.id'), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    cover_letter = db.Column(db.Text, nullable=False)
    proposed_price = db.Column(db.Float, nullable=False)
    estimated_duration = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum(ProposalStatusEnum), nullable=False, default=ProposalStatusEnum.pending)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    freelancer = db.relationship('User', foreign_keys=[freelancer_id])
    offer = db.relationship('Offer', foreign_keys=[offer_id])

    def to_dict(self):
        return {
            'id': self.id,
            'offer_id': self.offer_id,
            'freelancer_id': self.freelancer_id,
            'cover_letter': self.cover_letter,
            'proposed_price': self.proposed_price,
            'estimated_duration': self.estimated_duration,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'freelancer': self.freelancer.to_dict() if self.freelancer else None
        }

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    reviewer = db.relationship('User', foreign_keys=[reviewer_id])
    target = db.relationship('User', foreign_keys=[target_id])

    def to_dict(self):
        return {
            'id': self.id,
            'reviewer_id': self.reviewer_id,
            'target_id': self.target_id,
            'rating': self.rating,
            'comment': self.comment,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewer': self.reviewer.to_dict() if self.reviewer else None
        }
