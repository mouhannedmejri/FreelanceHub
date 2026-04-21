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
    portfolio = db.Column(db.JSON, default=list)
    certifications = db.Column(db.JSON, default=list)
    cv_filename = db.Column(db.String(255), default='')

    user = db.relationship('User', backref=db.backref('profile', uselist=False))

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
            'portfolio': self.portfolio or [],
            'certifications': self.certifications or [],
            'cv_filename': self.cv_filename or '',
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
