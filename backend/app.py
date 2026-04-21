from flask import Flask
from flask_cors import CORS
from config import Config
from models import (
    db, bcrypt, User, RoleEnum, Notification, NotificationTypeEnum,
    FreelancerProfile, Service, CategoryEnum, LevelEnum,
    Offer, OfferStatusEnum, LocationEnum, Conversation, Message,
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
    from routes.offers import offers_bp
    from routes.conversations import conversations_bp
    from routes.store import store_bp
    from routes.proposals import proposals_bp
    from routes.reviews import reviews_bp
    from routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(services_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(offers_bp)
    app.register_blueprint(conversations_bp)
    app.register_blueprint(store_bp)
    app.register_blueprint(proposals_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(admin_bp)

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
    """Seed users, freelancer profiles, services, offers, notifications and conversations for demo / testing."""
    _seed_users()
    _seed_profiles()
    _seed_services()
    _seed_offers()
    _seed_notifications()
    _seed_conversations()
    _seed_products()


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

        from models import Certification, PortfolioItem
        profile = FreelancerProfile(
            user_id=user.id,
            title=data['title'],
            bio=data['bio'],
            hourly_rate=data['hourly_rate'],
            location=data['location'],
            phone=data['phone'],
            skills=data['skills'],
        )
        db.session.add(profile)
        db.session.commit()

        for c in data.get('certifications', []):
            cert = Certification(user_id=user.id, name=c['name'], issuer=c['issuer'], year=str(c['year']))
            db.session.add(cert)
            
        for p in data.get('portfolio', []):
            item = PortfolioItem(user_id=user.id, title=p['title'], description=p['description'], skills=p.get('tags', []), image_url=p['image_url'])
            db.session.add(item)

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


# ── Offers ───────────────────────────────────────────────────────────────

def _seed_offers():
    if Offer.query.first():
        print('[OK] Seed offers already exist — skipping.')
        return

    client = User.query.filter_by(email='client@demo.com').first()
    if not client:
        print('[WARN] Client user not found — skipping offer seeding.')
        return

    offers = [
        {
            'client_id': client.id,
            'title': 'Développement d\'une Application Mobile React Native',
            'description': (
                'Nous recherchons un développeur React Native expérimenté pour créer '
                'une application mobile cross-platform (iOS & Android). '
                'L\'application doit inclure une authentification, un chat en temps réel '
                'et une intégration de paiement Stripe.'
            ),
            'category': CategoryEnum.developpement,
            'skills': ['React Native', 'TypeScript', 'Firebase', 'Stripe'],
            'budget_min': 2000,
            'budget_max': 5000,
            'duration': '1-3 mois',
            'location': LocationEnum.remote,
            'proposals_count': 8,
            'status': OfferStatusEnum.active,
        },
        {
            'client_id': client.id,
            'title': 'Refonte UI/UX d\'une Plateforme SaaS',
            'description': (
                'Notre plateforme SaaS B2B a besoin d\'une refonte complète de son interface. '
                'Nous cherchons un designer UI/UX senior capable de créer une expérience '
                'moderne, intuitive et accessible. Livraison de maquettes Figma et design system.'
            ),
            'category': CategoryEnum.design,
            'skills': ['Figma', 'UI Design', 'UX Research', 'Design System'],
            'budget_min': 1500,
            'budget_max': 3500,
            'duration': '1-4 semaines',
            'location': LocationEnum.hybrid,
            'proposals_count': 12,
            'status': OfferStatusEnum.active,
        },
        {
            'client_id': client.id,
            'title': 'Stratégie SEO & Content Marketing pour E-commerce',
            'description': (
                'Notre boutique en ligne cherche un expert SEO pour augmenter notre '
                'trafic organique. Mission : audit SEO complet, stratégie de contenu, '
                'optimisation on-page et création de 20 articles de blog optimisés par mois.'
            ),
            'category': CategoryEnum.marketing,
            'skills': ['SEO', 'Content Marketing', 'Google Analytics', 'Semrush'],
            'budget_min': 800,
            'budget_max': 1500,
            'duration': '3-6 mois',
            'location': LocationEnum.remote,
            'proposals_count': 5,
            'status': OfferStatusEnum.active,
        },
        {
            'client_id': client.id,
            'title': 'Rédaction de 50 Articles de Blog Tech',
            'description': (
                'Startup tech cherche un rédacteur web spécialisé pour produire '
                '50 articles de blog sur les thèmes de l\'IA, du cloud et de la cybersécurité. '
                'Articles de 1500 à 2000 mots, optimisés SEO, ton expert et accessible.'
            ),
            'category': CategoryEnum.redaction,
            'skills': ['Rédaction Web', 'SEO', 'Tech', 'Blog'],
            'budget_min': 1000,
            'budget_max': 2500,
            'duration': '1-3 mois',
            'location': LocationEnum.remote,
            'proposals_count': 3,
            'status': OfferStatusEnum.active,
        },
        {
            'client_id': client.id,
            'title': 'Développement Backend API Python/FastAPI',
            'description': (
                'Nous avons besoin d\'un développeur backend Python pour construire '
                'une API REST haute performance avec FastAPI, PostgreSQL et Redis. '
                'L\'API devra gérer 10k+ requêtes par seconde et inclure des tests complets.'
            ),
            'category': CategoryEnum.developpement,
            'skills': ['Python', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker'],
            'budget_min': 3000,
            'budget_max': 7000,
            'duration': '1-3 mois',
            'location': LocationEnum.onsite,
            'proposals_count': 15,
            'status': OfferStatusEnum.active,
        },
    ]

    for data in offers:
        offer = Offer(**data)
        db.session.add(offer)

    db.session.commit()
    print('[OK] Seed offers created.')


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

# ── Conversations ────────────────────────────────────────────────────────

def _seed_conversations():
    import datetime as _dt

    if Conversation.query.first():
        print('[OK] Seed conversations already exist — skipping.')
        return

    # Let's seed for 'freelancer@demo.com' as they are the demo user often
    user1 = User.query.filter_by(email='freelancer@demo.com').first()
    client = User.query.filter_by(email='client@demo.com').first()
    designer = User.query.filter_by(email='designer@demo.com').first()
    marketing = User.query.filter_by(email='marketing@demo.com').first()
    admin = User.query.filter_by(email='admin@demo.com').first()

    if not all([user1, client, designer, marketing, admin]):
        print('[WARN] Not all users found for conversations — skipping.')
        return

    now = _dt.datetime.now(_dt.timezone.utc)

    # 1. With Client
    conv1 = Conversation(
        participant_1_id=user1.id,
        participant_2_id=client.id,
        last_message='Parfait, je commence dès demain.',
        last_message_at=now - _dt.timedelta(minutes=10),
        unread_count_p1=0,
        unread_count_p2=1
    )
    db.session.add(conv1)
    db.session.commit()

    m1_1 = Message(conversation_id=conv1.id, sender_id=client.id, content='Bonjour, êtes-vous disponible pour une mission ?', created_at=now - _dt.timedelta(days=1), is_read=True)
    m1_2 = Message(conversation_id=conv1.id, sender_id=user1.id, content='Bonjour, oui tout à fait ! Quel est votre besoin ?', created_at=now - _dt.timedelta(hours=23), is_read=True)
    m1_3 = Message(conversation_id=conv1.id, sender_id=client.id, content='Nous voulons créer une app mobile. Avez-vous vu l\'offre ?', created_at=now - _dt.timedelta(hours=1), is_read=True)
    m1_4 = Message(conversation_id=conv1.id, sender_id=user1.id, content='Oui, je vous ai envoyé une proposition. Les délais me conviennent.', created_at=now - _dt.timedelta(minutes=30), is_read=True)
    m1_5 = Message(conversation_id=conv1.id, sender_id=client.id, content='Très bien, validé de notre côté.', created_at=now - _dt.timedelta(minutes=15), is_read=True)
    m1_6 = Message(conversation_id=conv1.id, sender_id=user1.id, content='Parfait, je commence dès demain.', created_at=now - _dt.timedelta(minutes=10), is_read=False)
    db.session.add_all([m1_1, m1_2, m1_3, m1_4, m1_5, m1_6])

    # 2. With Designer
    conv2 = Conversation(
        participant_1_id=designer.id,
        participant_2_id=user1.id,
        last_message='Peux-tu m\'envoyer les assets de la page d\'accueil ?',
        last_message_at=now - _dt.timedelta(hours=2),
        unread_count_p1=0,
        unread_count_p2=2
    )
    db.session.add(conv2)
    db.session.commit()

    m2_1 = Message(conversation_id=conv2.id, sender_id=user1.id, content='Salut ! Tu as pu avancer sur la maquette ?', created_at=now - _dt.timedelta(days=2), is_read=True)
    m2_2 = Message(conversation_id=conv2.id, sender_id=designer.id, content='Oui, je viens de finir. Je t\'envoie le lien Figma.', created_at=now - _dt.timedelta(days=2, hours=-1), is_read=True)
    m2_3 = Message(conversation_id=conv2.id, sender_id=designer.id, content='Dis-moi ce que tu en penses.', created_at=now - _dt.timedelta(days=2, hours=-1, minutes=-5), is_read=False)
    m2_4 = Message(conversation_id=conv2.id, sender_id=designer.id, content='Peux-tu m\'envoyer les assets de la page d\'accueil ?', created_at=now - _dt.timedelta(hours=2), is_read=False)
    db.session.add_all([m2_1, m2_2, m2_3, m2_4])

    # 3. With Marketing
    conv3 = Conversation(
        participant_1_id=user1.id,
        participant_2_id=marketing.id,
        last_message='Merci pour ces infos !',
        last_message_at=now - _dt.timedelta(days=5),
        unread_count_p1=0,
        unread_count_p2=0
    )
    db.session.add(conv3)
    db.session.commit()

    m3_1 = Message(conversation_id=conv3.id, sender_id=marketing.id, content='Hello, as-tu pu intégrer le script Google Analytics ?', created_at=now - _dt.timedelta(days=6), is_read=True)
    m3_2 = Message(conversation_id=conv3.id, sender_id=user1.id, content='Oui c\'est en prod depuis hier.', created_at=now - _dt.timedelta(days=5, hours=2), is_read=True)
    m3_3 = Message(conversation_id=conv3.id, sender_id=marketing.id, content='Super je vois les données remonter.', created_at=now - _dt.timedelta(days=5, hours=1), is_read=True)
    m3_4 = Message(conversation_id=conv3.id, sender_id=user1.id, content='Merci pour ces infos !', created_at=now - _dt.timedelta(days=5), is_read=True)
    db.session.add_all([m3_1, m3_2, m3_3, m3_4])

    # 4. With Admin
    conv4 = Conversation(
        participant_1_id=admin.id,
        participant_2_id=user1.id,
        last_message='Votre profil a été validé.',
        last_message_at=now - _dt.timedelta(days=10),
        unread_count_p1=0,
        unread_count_p2=0
    )
    db.session.add(conv4)
    db.session.commit()

    m4_1 = Message(conversation_id=conv4.id, sender_id=admin.id, content='Bienvenue sur FreelanceHub !', created_at=now - _dt.timedelta(days=10, hours=1), is_read=True)
    m4_2 = Message(conversation_id=conv4.id, sender_id=admin.id, content='Votre profil a été validé.', created_at=now - _dt.timedelta(days=10), is_read=True)
    db.session.add_all([m4_1, m4_2])

    db.session.commit()
    print('[OK] Seed conversations created.')

# ── Products ─────────────────────────────────────────────────────────────

def _seed_products():
    from models import Product, ProductCategoryEnum
    
    if Product.query.first():
        print('[OK] Seed products already exist — skipping.')
        return

    freelancer = User.query.filter_by(email='freelancer@demo.com').first()
    designer = User.query.filter_by(email='designer@demo.com').first()
    
    if not freelancer or not designer:
        print('[WARN] Users not found for products seeding — skipping.')
        return

    products = [
        Product(seller_id=freelancer.id, title="Angular Starter Kit Enterprise", description="Template complet avec auth, dashboard et composants.", category=ProductCategoryEnum.starter_kit, price=49.0, skills=["Angular", "TypeScript"], rating=4.8, sales_count=120, version="2.1.0", image_url="https://images.unsplash.com/photo-1555066931-4365d14bab8c?auto=format&fit=crop&q=80&w=600"),
        Product(seller_id=freelancer.id, title="Flask API Boilerplate", description="Structure RESTful complète avec JWT, SQLAlchemy et migrations.", category=ProductCategoryEnum.starter_kit, price=29.0, skills=["Python", "Flask", "SQL"], rating=4.9, sales_count=85, version="1.0.0", image_url="https://images.unsplash.com/photo-1526379095098-d400fd0bfce8?auto=format&fit=crop&q=80&w=600"),
        Product(seller_id=designer.id, title="Premium UI Kit Dark Mode", description="Composants Figma modernes pour dashboards SaaS.", category=ProductCategoryEnum.ui_kit, price=39.0, skills=["Figma", "UI/UX"], rating=5.0, sales_count=210, version="3.0.0", image_url="https://images.unsplash.com/photo-1561070791-2526d30994b5?auto=format&fit=crop&q=80&w=600"),
        Product(seller_id=designer.id, title="E-commerce App Template", description="Design complet d'app mobile E-commerce prêt à l'emploi.", category=ProductCategoryEnum.template, price=59.0, skills=["Figma", "Mobile App"], rating=4.7, sales_count=45, version="1.2.0", image_url="https://images.unsplash.com/photo-1512428559087-560fa5ceab42?auto=format&fit=crop&q=80&w=600"),
        Product(seller_id=designer.id, title="Architecture Plan Modulaire", description="Plans de base pour maisons modulaires écologiques.", category=ProductCategoryEnum.plan_archi, price=149.0, skills=["Architecture", "AutoCAD"], rating=4.5, sales_count=12, version="1.0.0", image_url="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=600"),
        Product(seller_id=freelancer.id, title="Vue.js Admin Dashboard", description="Template d'administration réactif avec Vuetify.", category=ProductCategoryEnum.template, price=35.0, skills=["Vue.js", "JavaScript"], rating=4.6, sales_count=60, version="2.0.0", image_url="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&q=80&w=600"),
    ]

    db.session.add_all(products)
    db.session.commit()
    print('[OK] Seed products created.')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
