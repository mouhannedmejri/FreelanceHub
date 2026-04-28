import os
import datetime
import uuid
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/freelancehub")

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def seed_db():
    client = MongoClient(MONGO_URI)
    db = client.get_database()

    # 1. Drop existing collections
    collections = db.list_collection_names()
    for coll in collections:
        db.drop_collection(coll)
    print(f"Dropped collections: {collections}")

    now = datetime.datetime.now(datetime.timezone.utc)

    # 2. Seed Users
    base_users = [
        {"full_name": "Alice Freelancer", "email": "freelancer@demo.com", "role": "freelancer"},
        {"full_name": "Bob Client", "email": "client@demo.com", "role": "client"},
        {"full_name": "Charlie Admin", "email": "admin@demo.com", "role": "admin"},
        {"full_name": "Sophie Martin", "email": "sophie@demo.com", "role": "freelancer"},
        {"full_name": "Thomas Dubois", "email": "thomas@demo.com", "role": "freelancer"},
        {"full_name": "Karim Benali", "email": "karim@demo.com", "role": "freelancer"},
        {"full_name": "Marie Leclerc", "email": "marie@demo.com", "role": "freelancer"},
        {"full_name": "Laura Petit", "email": "laura@demo.com", "role": "freelancer"},
        {"full_name": "Antoine Moreau", "email": "antoine@demo.com", "role": "freelancer"},
        {"full_name": "Claire Rousseau", "email": "claire@demo.com", "role": "freelancer"},
        {"full_name": "Pierre Laurent", "email": "pierre@demo.com", "role": "freelancer"},
        {"full_name": "Isabelle Durand", "email": "isabelle@demo.com", "role": "freelancer"},
        {"full_name": "Marc Simon", "email": "marc@demo.com", "role": "freelancer"}
    ]

    users_data = []
    for u in base_users:
        users_data.append({
            "full_name": u["full_name"],
            "email": u["email"],
            "password_hash": hash_password("demo1234"),
            "role": u["role"],
            "status": "active",
            "ban_reason": None,
            "last_login_at": now,
            "is_approved": True,
            "created_at": now
        })

    res_users = db.users.insert_many(users_data)
    print(f"Inserted {len(res_users.inserted_ids)} users.")

    user_map = { u["email"]: str(u["_id"]) for u in db.users.find() }
    name_map = { u["full_name"]: str(u["_id"]) for u in db.users.find() }

    # 3. Seed Freelancer Profiles
    profiles_data = [
        {
            "user_id": user_map["freelancer@demo.com"], "title": "Développeur Full Stack",
            "bio": "Développeur passionné avec plus de 8 ans d'expérience...",
            "hourly_rate": 45, "location": "Paris, France", "phone": "+33 6 12 34 56 78",
            "skills": ["React", "Angular", "Node.js"], "certifications": [], "portfolio": [],
            "cv_filename": "", "cv_size": 0, "avg_rating": 4.9, "total_reviews": 12
        }
    ]
    res_prof = db.freelancer_profiles.insert_many(profiles_data)
    print(f"Inserted {len(res_prof.inserted_ids)} freelancer profiles.")

    # 4. Seed Services
    services_list = [
        {
            "title": "Je développerai votre site web avec React et Tailwind CSS",
            "freelancer_name": "Sophie Martin", "category": "Développement", "level": "Expert",
            "price_from": 500, "rating": 4.9, "review_count": 127, "skills": ["React", "Tailwind", "TypeScript"]
        },
        {
            "title": "Création d'API REST avec Node.js et Express",
            "freelancer_name": "Thomas Dubois", "category": "Développement", "level": "Expert",
            "price_from": 350, "rating": 4.7, "review_count": 89, "skills": ["Node.js", "Express", "MongoDB"]
        },
        {
            "title": "Application mobile cross-platform avec Flutter",
            "freelancer_name": "Karim Benali", "category": "Développement", "level": "Intermédiaire",
            "price_from": 800, "rating": 4.5, "review_count": 43, "skills": ["Flutter", "Dart", "Firebase"]
        },
        {
            "title": "Intégration de paiement Stripe et PayPal",
            "freelancer_name": "Marie Leclerc", "category": "Développement", "level": "Expert",
            "price_from": 250, "rating": 4.8, "review_count": 67, "skills": ["Stripe", "PayPal", "Node.js"]
        },
        {
            "title": "Design UI/UX complet pour application mobile",
            "freelancer_name": "Laura Petit", "category": "Design", "level": "Expert",
            "price_from": 600, "rating": 5.0, "review_count": 201, "skills": ["Figma", "Adobe XD", "Prototyping"]
        },
        {
            "title": "Création de logo et identité visuelle",
            "freelancer_name": "Antoine Moreau", "category": "Design", "level": "Intermédiaire",
            "price_from": 150, "rating": 4.6, "review_count": 55, "skills": ["Illustrator", "Photoshop", "Branding"]
        },
        {
            "title": "Maquettes Figma pour site e-commerce",
            "freelancer_name": "Sophie Martin", "category": "Design", "level": "Expert",
            "price_from": 400, "rating": 4.9, "review_count": 38, "skills": ["Figma", "UI Design", "E-commerce"]
        },
        {
            "title": "Stratégie SEO et optimisation Google",
            "freelancer_name": "Claire Rousseau", "category": "Marketing", "level": "Expert",
            "price_from": 300, "rating": 4.7, "review_count": 112, "skills": ["SEO", "Google Analytics", "Content"]
        },
        {
            "title": "Gestion réseaux sociaux et création de contenu",
            "freelancer_name": "Pierre Laurent", "category": "Marketing", "level": "Intermédiaire",
            "price_from": 200, "rating": 4.4, "review_count": 29, "skills": ["Instagram", "TikTok", "Canva"]
        },
        {
            "title": "Campagnes Google Ads et Facebook Ads",
            "freelancer_name": "Claire Rousseau", "category": "Marketing", "level": "Expert",
            "price_from": 450, "rating": 4.8, "review_count": 76, "skills": ["Google Ads", "Meta Ads", "Analytics"]
        },
        {
            "title": "Rédaction d'articles SEO et blog professionnel",
            "freelancer_name": "Isabelle Durand", "category": "Rédaction", "level": "Expert",
            "price_from": 80, "rating": 4.9, "review_count": 143, "skills": ["SEO", "Copywriting", "WordPress"]
        },
        {
            "title": "Traduction FR/EN documents techniques",
            "freelancer_name": "Marc Simon", "category": "Rédaction", "level": "Intermédiaire",
            "price_from": 60, "rating": 4.6, "review_count": 34, "skills": ["Traduction", "Technique", "Relecture"]
        }
    ]

    services_data = []
    for s in services_list:
        services_data.append({
            "freelancer_id": name_map[s["freelancer_name"]],
            "title": s["title"],
            "description": s["title"] + " de haute qualité pour propulser vos projets.",
            "category": s["category"],
            "skills": s["skills"],
            "price_from": s["price_from"],
            "level": s["level"],
            "rating": s["rating"],
            "review_count": s["review_count"],
            "image_url": "",
            "approval_status": "approved",
            "created_at": now
        })

    # Add 2 pending services for approval requests
    services_data.extend([
        {
            "freelancer_id": name_map["Thomas Dubois"], "title": "Service en attente 1",
            "description": "En attente de validation...", "category": "Développement",
            "skills": ["Vue.js"], "price_from": 300, "level": "Intermédiaire",
            "rating": 0, "review_count": 0, "image_url": "",
            "approval_status": "pending", "created_at": now
        },
        {
            "freelancer_id": name_map["Laura Petit"], "title": "Service en attente 2",
            "description": "En attente de validation design...", "category": "Design",
            "skills": ["Figma"], "price_from": 200, "level": "Intermédiaire",
            "rating": 0, "review_count": 0, "image_url": "",
            "approval_status": "pending", "created_at": now
        }
    ])

    res_serv = db.services.insert_many(services_data)
    print(f"Inserted {len(res_serv.inserted_ids)} services.")
    
    pending_service_ids = [str(id) for idx, id in enumerate(res_serv.inserted_ids) if services_data[idx]["approval_status"] == "pending"]

    # 5. Seed Offers
    offers_data = [
        {
            "client_id": user_map["client@demo.com"], "title": "Développement App Mobile",
            "description": "Nous recherchons un développeur React Native pour une application e-commerce...", "category": "Développement",
            "skills": ["React Native", "TypeScript"], "budget_min": 2000, "budget_max": 5000, "duration": "1-3 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Création de site vitrine complet",
            "description": "Besoin d'un développeur pour un site vitrine en Vue.js...", "category": "Développement",
            "skills": ["Vue.js", "CSS"], "budget_min": 800, "budget_max": 1500, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Refonte Backend Python",
            "description": "Migration d'un backend existant vers Django et optimisation...", "category": "Développement",
            "skills": ["Python", "Django", "SQL"], "budget_min": 3000, "budget_max": 7000, "duration": "> 3 mois",
            "location": "Hybride", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Design Application Mobile Fintech",
            "description": "Nous cherchons un designer UX/UI senior pour concevoir notre app...", "category": "Design",
            "skills": ["Figma", "UX/UI"], "budget_min": 1500, "budget_max": 3000, "duration": "1-3 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Création de Logo & Charte Graphique",
            "description": "Pour une nouvelle marque de vêtements bio, nous voulons un logo moderne...", "category": "Design",
            "skills": ["Illustrator", "Branding"], "budget_min": 300, "budget_max": 600, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Campagne Google Ads B2B",
            "description": "Optimisation et gestion de campagnes d'acquisition B2B...", "category": "Marketing",
            "skills": ["Google Ads", "B2B"], "budget_min": 1000, "budget_max": 2500, "duration": "> 3 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Community Manager Instagram",
            "description": "Recherche CM pour animer une communauté pendant le lancement...", "category": "Marketing",
            "skills": ["Instagram", "Social Media"], "budget_min": 500, "budget_max": 1000, "duration": "1-3 mois",
            "location": "Hybride", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Stratégie SEO 2026",
            "description": "Audit SEO complet et recommandations techniques pour notre site...", "category": "Marketing",
            "skills": ["SEO", "Audit"], "budget_min": 1200, "budget_max": 2000, "duration": "< 1 mois",
            "location": "Sur site", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Rédaction Articles Tech",
            "description": "Besoin d'un rédacteur pour 5 articles techniques sur l'IA...", "category": "Rédaction",
            "skills": ["Rédaction technique", "IA"], "budget_min": 400, "budget_max": 800, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Copywriting Landing Page",
            "description": "Rédaction persuasive pour une page de vente SaaS...", "category": "Rédaction",
            "skills": ["Copywriting", "SaaS"], "budget_min": 200, "budget_max": 500, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "approved", "created_at": now
        },
        # 2 pending offers
        {
            "client_id": user_map["client@demo.com"], "title": "Offre en attente 1",
            "description": "En attente...", "category": "Développement",
            "skills": ["React"], "budget_min": 100, "budget_max": 200, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "pending", "created_at": now
        },
        {
            "client_id": user_map["client@demo.com"], "title": "Offre en attente 2",
            "description": "En attente...", "category": "Design",
            "skills": ["UI"], "budget_min": 100, "budget_max": 200, "duration": "< 1 mois",
            "location": "Remote", "proposals_count": 0, "status": "active", "approval_status": "pending", "created_at": now
        }
    ]
    res_off = db.offers.insert_many(offers_data)
    print(f"Inserted {len(res_off.inserted_ids)} offers.")
    offer_id_str = str(res_off.inserted_ids[0])
    
    pending_offer_ids = [str(id) for idx, id in enumerate(res_off.inserted_ids) if offers_data[idx]["approval_status"] == "pending"]

    # 6. Seed Projects (with milestones, tasks, deliverables)
    uid = lambda: str(uuid.uuid4())

    # ── Milestone/task IDs for Project 1 ──
    p1_m1, p1_m2, p1_m3 = uid(), uid(), uid()
    p1_t1, p1_t2, p1_t3, p1_t4, p1_t5, p1_t6 = uid(), uid(), uid(), uid(), uid(), uid()
    # ── Milestone/task IDs for Project 2 ──
    p2_m1, p2_m2 = uid(), uid()
    p2_t1, p2_t2, p2_t3, p2_t4 = uid(), uid(), uid(), uid()
    # ── Milestone/task IDs for Project 3 ──
    p3_m1, p3_m2 = uid(), uid()
    p3_t1, p3_t2, p3_t3 = uid(), uid(), uid()

    projects_data = [
        # ── Project 1: Développement App Mobile (active, rich) ──
        {
            "offer_id": offer_id_str, "client_id": user_map["client@demo.com"],
            "freelancer_id": user_map["freelancer@demo.com"],
            "title": "Développement App Mobile", "description": "Creation app React Native e-commerce",
            "status": "active", "budget": 3000,
            "started_at": now - datetime.timedelta(days=10),
            "deadline": now + datetime.timedelta(days=30),
            "completed_at": None, "client_rating": None, "freelancer_rating": None,
            "total_budget": 5000, "paid_amount": 1500,
            "milestones": [
                {"id": p1_m1, "title": "Design & Wireframes",
                 "due_date": (now + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
                 "status": "done", "deliverables": ["Maquettes Figma", "Guide de style"],
                 "budget_allocated": 1000},
                {"id": p1_m2, "title": "Développement Frontend",
                 "due_date": (now + datetime.timedelta(days=18)).strftime("%Y-%m-%d"),
                 "status": "in_progress", "deliverables": ["Code source React Native", "APK de test"],
                 "budget_allocated": 2500},
                {"id": p1_m3, "title": "Tests & Déploiement",
                 "due_date": (now + datetime.timedelta(days=28)).strftime("%Y-%m-%d"),
                 "status": "pending", "deliverables": ["Rapport de tests", "Build production"],
                 "budget_allocated": 1500}
            ],
            "tasks": [
                {"id": p1_t1, "milestone_id": p1_m1, "title": "Créer les maquettes écran d'accueil",
                 "description": "Design de la page d'accueil avec les composants principaux",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "done", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=8)).isoformat()},
                {"id": p1_t2, "milestone_id": p1_m1, "title": "Valider la charte graphique",
                 "description": "Finalisation des couleurs, typographies et icônes",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "done", "priority": "medium",
                 "due_date": (now + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=7)).isoformat()},
                {"id": p1_t3, "milestone_id": p1_m2, "title": "Implémenter la navigation",
                 "description": "React Navigation avec tabs et stack navigator",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "in_progress", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=12)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=5)).isoformat()},
                {"id": p1_t4, "milestone_id": p1_m2, "title": "Page produit et panier",
                 "description": "Écran de détails produit avec ajout au panier",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "todo", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=16)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=4)).isoformat()},
                {"id": p1_t5, "milestone_id": p1_m2, "title": "Intégration API de paiement",
                 "description": "Connexion Stripe pour les transactions",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "todo", "priority": "medium",
                 "due_date": (now + datetime.timedelta(days=18)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=3)).isoformat()},
                {"id": p1_t6, "milestone_id": p1_m3, "title": "Tests end-to-end",
                 "description": "Rédiger et exécuter les scénarios de test",
                 "assigned_to": user_map["freelancer@demo.com"], "status": "todo", "priority": "low",
                 "due_date": (now + datetime.timedelta(days=26)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=2)).isoformat()}
            ],
            "deliverables_list": [
                {"id": uid(), "milestone_id": p1_m1,
                 "file_url": "https://figma.com/file/example-mockups",
                 "file_name": "Maquettes_App_Mobile.fig",
                 "uploaded_by": user_map["freelancer@demo.com"],
                 "uploaded_at": (now - datetime.timedelta(days=2)).isoformat(),
                 "confirmed": True, "confirmed_at": (now - datetime.timedelta(days=1)).isoformat()},
                {"id": uid(), "milestone_id": p1_m1,
                 "file_url": "https://drive.google.com/file/style-guide",
                 "file_name": "Guide_Style_v2.pdf",
                 "uploaded_by": user_map["freelancer@demo.com"],
                 "uploaded_at": (now - datetime.timedelta(days=1)).isoformat(),
                 "confirmed": False}
            ],
            "progress_percent": 33.3
        },
        # ── Project 2: Refonte UI/UX (active) ──
        {
            "offer_id": offer_id_str, "client_id": user_map["client@demo.com"],
            "freelancer_id": user_map["sophie@demo.com"],
            "title": "Refonte UI/UX E-commerce", "description": "Refonte complète du site e-commerce",
            "status": "active", "budget": 1500,
            "started_at": now - datetime.timedelta(days=5),
            "deadline": now + datetime.timedelta(days=15),
            "completed_at": None, "client_rating": None, "freelancer_rating": None,
            "total_budget": 3000, "paid_amount": 800,
            "milestones": [
                {"id": p2_m1, "title": "Audit UX & Recherche",
                 "due_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
                 "status": "done", "deliverables": ["Rapport d'audit UX", "Personas"],
                 "budget_allocated": 1000},
                {"id": p2_m2, "title": "Nouvelles Maquettes",
                 "due_date": (now + datetime.timedelta(days=12)).strftime("%Y-%m-%d"),
                 "status": "in_progress", "deliverables": ["Maquettes desktop", "Maquettes mobile"],
                 "budget_allocated": 2000}
            ],
            "tasks": [
                {"id": p2_t1, "milestone_id": p2_m1, "title": "Audit de l'interface actuelle",
                 "description": "Analyser les parcours utilisateurs existants",
                 "assigned_to": user_map["sophie@demo.com"], "status": "done", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=2)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=4)).isoformat()},
                {"id": p2_t2, "milestone_id": p2_m1, "title": "Créer les personas",
                 "description": "Définir 3 personas principaux",
                 "assigned_to": user_map["sophie@demo.com"], "status": "done", "priority": "medium",
                 "due_date": (now + datetime.timedelta(days=3)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=3)).isoformat()},
                {"id": p2_t3, "milestone_id": p2_m2, "title": "Maquetter la page d'accueil",
                 "description": "Design responsive de la homepage",
                 "assigned_to": user_map["sophie@demo.com"], "status": "in_progress", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=8)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=2)).isoformat()},
                {"id": p2_t4, "milestone_id": p2_m2, "title": "Maquetter le tunnel d'achat",
                 "description": "Optimiser la conversion du checkout",
                 "assigned_to": user_map["sophie@demo.com"], "status": "review", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=11)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=1)).isoformat()}
            ],
            "deliverables_list": [
                {"id": uid(), "milestone_id": p2_m1,
                 "file_url": "https://drive.google.com/file/ux-audit",
                 "file_name": "Rapport_Audit_UX.pdf",
                 "uploaded_by": user_map["sophie@demo.com"],
                 "uploaded_at": (now - datetime.timedelta(days=1)).isoformat(),
                 "confirmed": True, "confirmed_at": now.isoformat()}
            ],
            "progress_percent": 50.0
        },
        # ── Project 3: API Backend Node.js (active) ──
        {
            "offer_id": offer_id_str, "client_id": user_map["client@demo.com"],
            "freelancer_id": user_map["thomas@demo.com"],
            "title": "API Backend Node.js", "description": "Création API REST complète",
            "status": "active", "budget": 2000,
            "started_at": now - datetime.timedelta(days=3),
            "deadline": now + datetime.timedelta(days=20),
            "completed_at": None, "client_rating": None, "freelancer_rating": None,
            "total_budget": 4000, "paid_amount": 0,
            "milestones": [
                {"id": p3_m1, "title": "Architecture & Setup",
                 "due_date": (now + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
                 "status": "in_progress", "deliverables": ["Schéma architecture", "Setup CI/CD"],
                 "budget_allocated": 1500},
                {"id": p3_m2, "title": "Endpoints CRUD",
                 "due_date": (now + datetime.timedelta(days=18)).strftime("%Y-%m-%d"),
                 "status": "pending", "deliverables": ["Documentation API", "Collection Postman"],
                 "budget_allocated": 2500}
            ],
            "tasks": [
                {"id": p3_t1, "milestone_id": p3_m1, "title": "Configurer Express + MongoDB",
                 "description": "Setup du projet Node.js avec TypeScript",
                 "assigned_to": user_map["thomas@demo.com"], "status": "in_progress", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=4)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=2)).isoformat()},
                {"id": p3_t2, "milestone_id": p3_m1, "title": "Modèles de données",
                 "description": "Schéma Mongoose pour users, products, orders",
                 "assigned_to": user_map["thomas@demo.com"], "status": "todo", "priority": "high",
                 "due_date": (now + datetime.timedelta(days=5)).strftime("%Y-%m-%d"),
                 "created_at": (now - datetime.timedelta(days=1)).isoformat()},
                {"id": p3_t3, "milestone_id": p3_m2, "title": "Endpoints authentification",
                 "description": "Login, register, JWT, refresh token",
                 "assigned_to": user_map["thomas@demo.com"], "status": "todo", "priority": "medium",
                 "due_date": (now + datetime.timedelta(days=10)).strftime("%Y-%m-%d"),
                 "created_at": now.isoformat()}
            ],
            "deliverables_list": [],
            "progress_percent": 0
        },
        # ── Project 4: Intégration Stripe (completed) ──
        {
            "offer_id": offer_id_str, "client_id": user_map["client@demo.com"],
            "freelancer_id": user_map["karim@demo.com"],
            "title": "Intégration Stripe", "description": "Module de paiement",
            "status": "completed", "budget": 500,
            "started_at": now - datetime.timedelta(days=40),
            "deadline": now - datetime.timedelta(days=30),
            "completed_at": now - datetime.timedelta(days=35),
            "client_rating": 5, "freelancer_rating": 4,
            "total_budget": 500, "paid_amount": 500,
            "milestones": [
                {"id": uid(), "title": "Intégration complète",
                 "due_date": (now - datetime.timedelta(days=32)).strftime("%Y-%m-%d"),
                 "status": "done", "deliverables": ["Module Stripe"],
                 "budget_allocated": 500}
            ],
            "tasks": [], "deliverables_list": [], "progress_percent": 100
        },
        # ── Project 5: Design Logo (completed) ──
        {
            "offer_id": offer_id_str, "client_id": user_map["client@demo.com"],
            "freelancer_id": user_map["marie@demo.com"],
            "title": "Design Logo", "description": "Création logo entreprise",
            "status": "completed", "budget": 300,
            "started_at": now - datetime.timedelta(days=20),
            "deadline": now - datetime.timedelta(days=10),
            "completed_at": now - datetime.timedelta(days=12),
            "client_rating": 4, "freelancer_rating": 5,
            "total_budget": 300, "paid_amount": 300,
            "milestones": [
                {"id": uid(), "title": "Propositions de logo",
                 "due_date": (now - datetime.timedelta(days=15)).strftime("%Y-%m-%d"),
                 "status": "done", "deliverables": ["3 propositions logo"],
                 "budget_allocated": 200},
                {"id": uid(), "title": "Livraison finale",
                 "due_date": (now - datetime.timedelta(days=11)).strftime("%Y-%m-%d"),
                 "status": "done", "deliverables": ["Fichiers AI/SVG/PNG"],
                 "budget_allocated": 100}
            ],
            "tasks": [], "deliverables_list": [], "progress_percent": 100
        }
    ]
    res_proj = db.projects.insert_many(projects_data)
    print(f"Inserted {len(res_proj.inserted_ids)} projects.")
    
    # Update user earnings and projects count for realistic stats
    db.freelancer_profiles.update_one({"user_id": user_map["karim@demo.com"]}, {"$inc": {"total_earnings": 500, "completed_projects": 1}})
    db.freelancer_profiles.update_one({"user_id": user_map["marie@demo.com"]}, {"$inc": {"total_earnings": 300, "completed_projects": 1}})

    # 7. Seed Claims
    claims_data = [
        {
            "claimant_id": user_map["client@demo.com"], "target_id": user_map["freelancer@demo.com"], 
            "project_id": str(res_proj.inserted_ids[0]), "type": "quality",
            "title": "Retard de livraison", "description": "Le projet n'avance pas...",
            "status": "open", "priority": "medium", "admin_note": "",
            "created_at": now, "updated_at": now, "resolved_at": None
        },
        {
            "claimant_id": user_map["sophie@demo.com"], "target_id": user_map["client@demo.com"], 
            "project_id": str(res_proj.inserted_ids[1]), "type": "payment",
            "title": "Paiement non reçu", "description": "Le client ne répond plus...",
            "status": "in_review", "priority": "high", "admin_note": "Contacting client",
            "created_at": now, "updated_at": now, "resolved_at": None
        },
        {
            "claimant_id": user_map["thomas@demo.com"], "target_id": user_map["client@demo.com"], 
            "project_id": None, "type": "behavior",
            "title": "Comportement inapproprié", "description": "Messages insultants...",
            "status": "resolved", "priority": "urgent", "admin_note": "Avertissement envoyé au client.",
            "created_at": now - datetime.timedelta(days=5), "updated_at": now, "resolved_at": now
        }
    ]
    res_claims = db.claims.insert_many(claims_data)
    print(f"Inserted {len(res_claims.inserted_ids)} claims.")

    # 8. Seed Approval Requests
    approvals_data = [
        {
            "requester_id": name_map["Thomas Dubois"], "type": "service", "reference_id": pending_service_ids[0],
            "status": "pending", "admin_note": "", "created_at": now, "reviewed_at": None
        },
        {
            "requester_id": name_map["Laura Petit"], "type": "service", "reference_id": pending_service_ids[1],
            "status": "pending", "admin_note": "", "created_at": now, "reviewed_at": None
        },
        {
            "requester_id": user_map["client@demo.com"], "type": "offer", "reference_id": pending_offer_ids[0],
            "status": "pending", "admin_note": "", "created_at": now, "reviewed_at": None
        },
        {
            "requester_id": user_map["client@demo.com"], "type": "offer", "reference_id": pending_offer_ids[1],
            "status": "pending", "admin_note": "", "created_at": now, "reviewed_at": None
        }
    ]
    res_approvals = db.approval_requests.insert_many(approvals_data)
    print(f"Inserted {len(res_approvals.inserted_ids)} approval requests.")


    # 7. Seed Notifications
    notifs_data = [
        { "user_id": user_map["freelancer@demo.com"], "type": "message", "title": "Nouveau message", "body": "Salut", "is_read": False, "created_at": now },
        { "user_id": user_map["client@demo.com"], "type": "offer", "title": "Offre publiée", "body": "Votre offre est en ligne.", "is_read": False, "created_at": now }
    ]
    res_notif = db.notifications.insert_many(notifs_data)
    print(f"Inserted {len(res_notif.inserted_ids)} notifications.")
    
    # 8. Seed Conversations & Messages
    conv_data = [
        {
            "participant_ids": [user_map["freelancer@demo.com"], user_map["client@demo.com"]],
            "offer_id": offer_id_str,
            "last_message": "Parfait, je commence dès demain.",
            "last_message_at": now,
            "unread_counts": { user_map["freelancer@demo.com"]: 0, user_map["client@demo.com"]: 1 }
        }
    ]
    res_conv = db.conversations.insert_many(conv_data)
    print(f"Inserted {len(res_conv.inserted_ids)} conversations.")
    
    msg_data = [
        { "conversation_id": str(res_conv.inserted_ids[0]), "sender_id": user_map["freelancer@demo.com"], "content": "Parfait, je commence dès demain.", "created_at": now, "is_read": False }
    ]
    res_msg = db.messages.insert_many(msg_data)
    print(f"Inserted {len(res_msg.inserted_ids)} messages.")

    # 9. Seed Follows (demo follow relationships)
    follows_data = [
        {"follower_id": user_map["client@demo.com"], "following_id": user_map["freelancer@demo.com"], "created_at": now},
        {"follower_id": user_map["client@demo.com"], "following_id": user_map["sophie@demo.com"], "created_at": now},
        {"follower_id": user_map["thomas@demo.com"], "following_id": user_map["freelancer@demo.com"], "created_at": now},
        {"follower_id": user_map["karim@demo.com"], "following_id": user_map["freelancer@demo.com"], "created_at": now},
        {"follower_id": user_map["marie@demo.com"], "following_id": user_map["freelancer@demo.com"], "created_at": now},
    ]
    res_follows = db.follows.insert_many(follows_data)
    print(f"Inserted {len(res_follows.inserted_ids)} follows.")

    # Indexes
    db.users.create_index("email", unique=True)
    db.offers.create_index("client_id")
    db.offers.create_index("status")
    db.proposals.create_index("offer_id")
    db.proposals.create_index("freelancer_id")
    db.messages.create_index("conversation_id")
    db.notifications.create_index("user_id")
    db.projects.create_index([("client_id", 1), ("status", 1)])
    db.projects.create_index([("freelancer_id", 1), ("status", 1)])
    db.claims.create_index("status")
    db.approval_requests.create_index("status")
    db.user_bans.create_index("user_id")
    db.follows.create_index([("follower_id", 1), ("following_id", 1)], unique=True)
    db.follows.create_index("following_id")
    
    print("Indexes created. Seeding completed successfully.")

if __name__ == "__main__":
    seed_db()
