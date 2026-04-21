from flask import Flask
from flask_cors import CORS
from config import Config
from models import (
    db, bcrypt, User, RoleEnum, Notification, NotificationTypeEnum,
    FreelancerProfile, Service, CategoryEnum, LevelEnum,
)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # Register blueprints
    from routes.auth import auth_bp
    from routes.home import home_bp
    from routes.notifications import notifications_bp
    from routes.services import services_bp
    from routes.users import users_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(users_bp)

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'message': 'FreelanceHub API is running'}

    # Create tables and seed data
    with app.app_context():
        db.create_all()
        seed_data()

    return app


def seed_data():
    """Seed users, freelancer profiles, services, and notifications for demo / testing."""
    _seed_users()
    _seed_profiles()
    _seed_services()
    _seed_notifications()


# ── Users ────────────────────────────────────────────────────────────────

def _seed_users():
    seeds = [
        {
            'full_name': 'Alice Freelancer',
            'email': 'freelancer@demo.com',
            'password': 'password123',
            'role': RoleEnum.freelancer,
            'is_approved': True,
        },
        {
            'full_name': 'Bob Client',
            'email': 'client@demo.com',
            'password': 'password123',
            'role': RoleEnum.client,
            'is_approved': True,
        },
        {
            'full_name': 'Charlie Admin',
            'email': 'admin@demo.com',
            'password': 'password123',
            'role': RoleEnum.admin,
            'is_approved': True,
        },
        {
            'full_name': 'David Designer',
            'email': 'designer@demo.com',
            'password': 'password123',
            'role': RoleEnum.freelancer,
            'is_approved': True,
        },
        {
            'full_name': 'Eve Marketing',
            'email': 'marketing@demo.com',
            'password': 'password123',
            'role': RoleEnum.freelancer,
            'is_approved': True,
        },
        {
            'full_name': 'Frank Rédacteur',
            'email': 'redacteur@demo.com',
            'password': 'password123',
            'role': RoleEnum.freelancer,
            'is_approved': True,
        },
    ]

    for seed in seeds:
        if not User.query.filter_by(email=seed['email']).first():
            user = User(
                full_name=seed['full_name'],
                email=seed['email'],
                role=seed['role'],
                is_approved=seed['is_approved'],
            )
            user.set_password(seed['password'])
            db.session.add(user)

    db.session.commit()
    print('[OK] Seed users created (or already exist).')


# ── Freelancer Profiles ──────────────────────────────────────────────────

def _seed_profiles():
    profiles = {
        'freelancer@demo.com': {
            'title': 'Développeur Full Stack',
            'bio': (
                'Développeur passionné avec plus de 8 ans d\'expérience dans la '
                'création d\'applications web et mobiles modernes. Spécialisé en '
                'React, Angular et Node.js, je livre des solutions performantes '
                'et évolutives pour startups et entreprises.'
            ),
            'hourly_rate': 45,
            'location': 'Paris, France',
            'phone': '+33 6 12 34 56 78',
            'skills': ['React', 'Angular', 'TypeScript', 'Node.js', 'Python', 'PostgreSQL', 'Docker', 'AWS'],
            'portfolio': [
                {
                    'title': 'Plateforme E-commerce',
                    'description': 'Marketplace complète avec paiement Stripe et gestion des commandes en temps réel.',
                    'image_url': 'https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=600&h=400&fit=crop',
                    'tags': ['React', 'Stripe', 'Node.js'],
                },
                {
                    'title': 'Dashboard Analytics',
                    'description': 'Tableau de bord temps réel avec visualisations D3.js pour une entreprise SaaS.',
                    'image_url': 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=600&h=400&fit=crop',
                    'tags': ['D3.js', 'React', 'API REST'],
                },
            ],
            'certifications': [
                {'name': 'AWS Solutions Architect', 'issuer': 'Amazon Web Services', 'year': 2024},
                {'name': 'React Professional Developer', 'issuer': 'Meta', 'year': 2023},
            ],
        },
        'designer@demo.com': {
            'title': 'Designer UI/UX Senior',
            'bio': (
                'Designer UI/UX créatif avec un œil aiguisé pour les détails. '
                'Je crée des interfaces intuitives et magnifiques qui ravissent '
                'les utilisateurs. Expert Figma et Adobe Creative Suite.'
            ),
            'hourly_rate': 55,
            'location': 'Lyon, France',
            'phone': '+33 6 98 76 54 32',
            'skills': ['Figma', 'Adobe XD', 'Illustrator', 'Photoshop', 'UI Design', 'Prototypage', 'Design System'],
            'portfolio': [
                {
                    'title': 'App Bancaire Mobile',
                    'description': 'Refonte complète de l\'interface d\'une application bancaire mobile.',
                    'image_url': 'https://images.unsplash.com/photo-1563986768609-322da13575f2?w=600&h=400&fit=crop',
                    'tags': ['UI/UX', 'Mobile', 'Figma'],
                },
                {
                    'title': 'Identité Visuelle Startup',
                    'description': 'Création de l\'identité visuelle complète pour une startup tech innovante.',
                    'image_url': 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&h=400&fit=crop',
                    'tags': ['Branding', 'Logo', 'Charte'],
                },
            ],
            'certifications': [
                {'name': 'Google UX Design Certificate', 'issuer': 'Google', 'year': 2024},
                {'name': 'Adobe Certified Expert', 'issuer': 'Adobe', 'year': 2023},
            ],
        },
        'marketing@demo.com': {
            'title': 'Consultante Marketing Digital',
            'bio': (
                'Experte en marketing digital et SEO, j\'aide les entreprises à '
                'augmenter leur visibilité en ligne et à convertir plus de prospects. '
                'Spécialisée en stratégie de contenu et publicité payante.'
            ),
            'hourly_rate': 40,
            'location': 'Marseille, France',
            'phone': '+33 6 55 44 33 22',
            'skills': ['SEO', 'Google Ads', 'Analytics', 'Social Media', 'Email Marketing', 'Content Strategy'],
            'portfolio': [
                {
                    'title': 'Campagne SEO E-commerce',
                    'description': 'Stratégie SEO complète ayant entraîné une hausse de 200% du trafic organique.',
                    'image_url': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&h=400&fit=crop',
                    'tags': ['SEO', 'Analytics', 'E-commerce'],
                },
            ],
            'certifications': [
                {'name': 'Google Analytics Certified', 'issuer': 'Google', 'year': 2024},
                {'name': 'HubSpot Inbound Marketing', 'issuer': 'HubSpot', 'year': 2023},
            ],
        },
        'redacteur@demo.com': {
            'title': 'Rédacteur Web & Copywriter',
            'bio': (
                'Rédacteur web professionnel spécialisé en contenu SEO et copywriting. '
                'Je produis des articles de blog, des pages de vente et du contenu '
                'éditorial engageant qui convertit.'
            ),
            'hourly_rate': 35,
            'location': 'Bordeaux, France',
            'phone': '+33 6 11 22 33 44',
            'skills': ['Rédaction Web', 'SEO', 'Copywriting', 'Blog', 'Content Marketing', 'Storytelling'],
            'portfolio': [
                {
                    'title': 'Blog Tech Startup',
                    'description': 'Stratégie éditoriale et rédaction de 50+ articles de blog optimisés SEO.',
                    'image_url': 'https://images.unsplash.com/photo-1455390582262-044cdead277a?w=600&h=400&fit=crop',
                    'tags': ['Blog', 'SEO', 'Tech'],
                },
            ],
            'certifications': [
                {'name': 'Content Marketing Certified', 'issuer': 'HubSpot', 'year': 2024},
            ],
        },
    }

    for email, data in profiles.items():
        user = User.query.filter_by(email=email).first()
        if not user:
            continue
        if FreelancerProfile.query.filter_by(user_id=user.id).first():
            continue  # already seeded

        profile = FreelancerProfile(
            user_id=user.id,
            title=data['title'],
            bio=data['bio'],
            hourly_rate=data['hourly_rate'],
            location=data['location'],
            phone=data['phone'],
            skills=data['skills'],
            portfolio=data['portfolio'],
            certifications=data['certifications'],
        )
        db.session.add(profile)

    db.session.commit()
    print('[OK] Seed freelancer profiles created (or already exist).')


# ── Services ─────────────────────────────────────────────────────────────

def _seed_services():
    if Service.query.first():
        print('[OK] Seed services already exist — skipping.')
        return

    user_map = {
        email: User.query.filter_by(email=email).first()
        for email in [
            'freelancer@demo.com', 'designer@demo.com',
            'marketing@demo.com', 'redacteur@demo.com',
        ]
    }

    services = [
        {
            'freelancer_id': user_map['freelancer@demo.com'].id,
            'title': 'Développement d\'Applications Web React',
            'description': (
                'Je développe des applications web modernes et performantes '
                'avec React, Next.js et TypeScript. Architecture propre, '
                'tests unitaires et déploiement CI/CD inclus.'
            ),
            'category': CategoryEnum.developpement,
            'cover_image_url': 'https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=800&h=400&fit=crop',
            'tags': ['React', 'TypeScript', 'Next.js', 'Tailwind CSS'],
            'level': LevelEnum.expert,
            'price_from': 500,
            'rating': 4.9,
            'review_count': 127,
        },
        {
            'freelancer_id': user_map['freelancer@demo.com'].id,
            'title': 'API REST & Microservices Node.js',
            'description': (
                'Conception et développement d\'API REST robustes et de '
                'microservices avec Node.js, Express et MongoDB. Documentation '
                'Swagger et tests d\'intégration fournis.'
            ),
            'category': CategoryEnum.developpement,
            'cover_image_url': 'https://images.unsplash.com/photo-1627398242454-45a1465c2479?w=800&h=400&fit=crop',
            'tags': ['Node.js', 'Express', 'MongoDB', 'Docker'],
            'level': LevelEnum.senior,
            'price_from': 400,
            'rating': 4.7,
            'review_count': 89,
        },
        {
            'freelancer_id': user_map['designer@demo.com'].id,
            'title': 'Design UI/UX Mobile & Web',
            'description': (
                'Création d\'interfaces utilisateur intuitives et modernes '
                'pour applications mobiles et web. Wireframes, prototypes '
                'interactifs et design system complet.'
            ),
            'category': CategoryEnum.design,
            'cover_image_url': 'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=800&h=400&fit=crop',
            'tags': ['Figma', 'Adobe XD', 'UI Design', 'Prototypage'],
            'level': LevelEnum.expert,
            'price_from': 600,
            'rating': 4.9,
            'review_count': 156,
        },
        {
            'freelancer_id': user_map['designer@demo.com'].id,
            'title': 'Création de Logo & Identité Visuelle',
            'description': (
                'Conception de logos uniques et de chartes graphiques complètes '
                'pour donner à votre marque une identité forte et mémorable.'
            ),
            'category': CategoryEnum.design,
            'cover_image_url': 'https://images.unsplash.com/photo-1626785774573-4b799315345d?w=800&h=400&fit=crop',
            'tags': ['Illustrator', 'Logo', 'Branding', 'Charte Graphique'],
            'level': LevelEnum.junior,
            'price_from': 150,
            'rating': 4.5,
            'review_count': 34,
        },
        {
            'freelancer_id': user_map['marketing@demo.com'].id,
            'title': 'Stratégie Marketing Digital & SEO',
            'description': (
                'Élaboration de stratégies marketing digitales sur mesure. '
                'Audit SEO, campagnes Google Ads, gestion des réseaux sociaux '
                'et analyse des performances.'
            ),
            'category': CategoryEnum.marketing,
            'cover_image_url': 'https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&h=400&fit=crop',
            'tags': ['SEO', 'Google Ads', 'Analytics', 'Social Media'],
            'level': LevelEnum.senior,
            'price_from': 350,
            'rating': 4.8,
            'review_count': 72,
        },
        {
            'freelancer_id': user_map['redacteur@demo.com'].id,
            'title': 'Rédaction de Contenu Web & SEO',
            'description': (
                'Rédaction d\'articles de blog, de pages de vente et de '
                'contenu web optimisé SEO. Recherche de mots-clés et '
                'stratégie éditoriale pour booster votre visibilité.'
            ),
            'category': CategoryEnum.redaction,
            'cover_image_url': 'https://images.unsplash.com/photo-1455390582262-044cdead277a?w=800&h=400&fit=crop',
            'tags': ['Rédaction Web', 'SEO', 'Blog', 'Copywriting'],
            'level': LevelEnum.senior,
            'price_from': 200,
            'rating': 4.6,
            'review_count': 58,
        },
    ]

    for data in services:
        service = Service(**data)
        db.session.add(service)

    db.session.commit()
    print('[OK] Seed services created.')


# ── Notifications ────────────────────────────────────────────────────────

def _seed_notifications():
    import datetime as _dt

    # Only seed if no notifications exist yet
    if Notification.query.first():
        print('[OK] Seed notifications already exist — skipping.')
        return

    now = _dt.datetime.now(_dt.timezone.utc)
    users = User.query.all()

    samples = [
        {
            'type': NotificationTypeEnum.message,
            'title': 'Nouveau message reçu',
            'body': 'Un client vous a envoyé un message concernant votre profil.',
            'delta': _dt.timedelta(minutes=5),
        },
        {
            'type': NotificationTypeEnum.offer,
            'title': 'Nouvelle offre disponible',
            'body': 'Une offre correspondant à vos compétences a été publiée.',
            'delta': _dt.timedelta(hours=2),
        },
        {
            'type': NotificationTypeEnum.payment,
            'title': 'Paiement reçu',
            'body': 'Vous avez reçu un paiement de 150€ pour votre dernière mission.',
            'delta': _dt.timedelta(days=1),
        },
        {
            'type': NotificationTypeEnum.review,
            'title': 'Nouvel avis client',
            'body': 'Un client vous a laissé un avis 5 étoiles. Félicitations!',
            'delta': _dt.timedelta(days=3),
        },
    ]

    for user in users:
        for s in samples:
            notif = Notification(
                user_id=user.id,
                type=s['type'],
                title=s['title'],
                body=s['body'],
                is_read=False,
                created_at=now - s['delta'],
            )
            db.session.add(notif)

    db.session.commit()
    print(f'[OK] Seed notifications created for {len(users)} users.')


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
