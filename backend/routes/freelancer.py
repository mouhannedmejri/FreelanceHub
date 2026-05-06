from flask import Blueprint, request, jsonify, current_app
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime
import os
import uuid
from dateutil.relativedelta import relativedelta
from werkzeug.utils import secure_filename

from app import mongo, serialize, serialize_list
from stats_helper import get_freelancer_stats

freelancer_bp = Blueprint('freelancer', __name__, url_prefix='/api/freelancer')
ALLOWED_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def freelancer_required(f):
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        current_user = mongo.db.users.find_one({"_id": ObjectId(user_id)})
        if not current_user or current_user.get("role") != "freelancer":
            return jsonify({'error': 'Freelancer access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated


def _get_profile(user_id: str):
    profile = mongo.db.freelancer_profiles.find_one({"user_id": user_id})
    if profile:
        return profile
    profile = {
        "user_id": user_id,
        "portfolio_projects": [],
        "certifications": [],
        "skills_endorsed": [],
        "video_intro_url": "",
        "availability_status": "available",
        "languages": [],
    }
    mongo.db.freelancer_profiles.insert_one(profile)
    return profile


def _find_project(projects, project_id):
    for idx, p in enumerate(projects):
        if str(p.get("id")) == str(project_id):
            return idx, p
    return -1, None


@freelancer_bp.route('/dashboard', methods=['GET'])
@freelancer_required
def get_dashboard(current_user):
    freelancer_id = str(current_user["_id"])
    stats = get_freelancer_stats(freelancer_id)

    active_projects = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "active"}).sort("created_at", -1).limit(5))
    for p in active_projects:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        if client:
            p["client"] = {
                "id": str(client["_id"]),
                "full_name": client.get("full_name"),
                "avatar_initials": client.get("full_name", "?")[0].upper() if client.get("full_name") else "?"
            }

    recent_proposals = list(mongo.db.proposals.find({"freelancer_id": freelancer_id}).sort("created_at", -1).limit(5))
    for prop in recent_proposals:
        offer = mongo.db.offers.find_one({"_id": ObjectId(prop["offer_id"])})
        if offer:
            prop["offer_title"] = offer.get("title")

    recent_reviews = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "completed", "freelancer_rating": {"$ne": None}}).sort("completed_at", -1).limit(3))
    reviews = []
    for p in recent_reviews:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        reviews.append({
            "project_title": p.get("title"),
            "rating": p.get("freelancer_rating"),
            "comment": p.get("freelancer_review_comment", ""),
            "date": p.get("completed_at"),
            "client": {
                "full_name": client.get("full_name") if client else "Unknown",
                "avatar_initials": client.get("full_name", "?")[0].upper() if client and client.get("full_name") else "?"
            }
        })

    return jsonify({
        "stats": stats,
        "active_projects": serialize_list(active_projects),
        "recent_proposals": serialize_list(recent_proposals),
        "recent_reviews": reviews
    }), 200


@freelancer_bp.route('/projects', methods=['GET'])
@freelancer_required
def get_projects(current_user):
    freelancer_id = str(current_user["_id"])
    status = request.args.get('status', 'all').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = {"freelancer_id": freelancer_id}
    if status != 'all':
        query["status"] = status

    total = mongo.db.projects.count_documents(query)
    projects = list(mongo.db.projects.find(query).sort("created_at", -1).skip((page - 1) * per_page).limit(per_page))

    for p in projects:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        if client:
            p["client"] = {
                "id": str(client["_id"]),
                "full_name": client.get("full_name"),
                "avatar_initials": client.get("full_name", "?")[0].upper() if client.get("full_name") else "?"
            }

        offer = mongo.db.offers.find_one({"_id": ObjectId(p["offer_id"])})
        if offer:
            p["offer"] = serialize(offer)

    return jsonify({"projects": serialize_list(projects), "total": total, "page": page, "per_page": per_page}), 200


@freelancer_bp.route('/earnings', methods=['GET'])
@freelancer_required
def get_earnings(current_user):
    freelancer_id = str(current_user["_id"])
    period = request.args.get('period', 'month')
    now = datetime.datetime.now(datetime.timezone.utc)

    pipeline_total = [{"$match": {"freelancer_id": freelancer_id, "status": "completed"}}, {"$group": {"_id": None, "total": {"$sum": "$budget"}}}]
    res_total = list(mongo.db.projects.aggregate(pipeline_total))
    total_earned = res_total[0]["total"] if res_total else 0

    if period == 'month':
        start_this = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
        start_last = start_this - relativedelta(months=1)
    else:
        start_this = datetime.datetime(now.year, 1, 1, tzinfo=datetime.timezone.utc)
        start_last = datetime.datetime(now.year - 1, 1, 1, tzinfo=datetime.timezone.utc)

    def sum_budget(query):
        res = list(mongo.db.projects.aggregate([{"$match": query}, {"$group": {"_id": None, "total": {"$sum": "$budget"}}}]))
        return res[0]["total"] if res else 0

    this_period = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": start_this}})
    last_period = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": start_last, "$lt": start_this}})

    by_month = []
    for i in range(5, -1, -1):
        m_start = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc) - relativedelta(months=i)
        m_end = m_start + relativedelta(months=1)
        amount = sum_budget({"freelancer_id": freelancer_id, "status": "completed", "completed_at": {"$gte": m_start, "$lt": m_end}})
        by_month.append({"month": m_start.strftime("%b"), "amount": amount})

    by_project = []
    projects = list(mongo.db.projects.find({"freelancer_id": freelancer_id, "status": "completed"}).sort("completed_at", -1))
    for p in projects:
        by_project.append({"title": p.get("title"), "amount": p.get("budget"), "date": p.get("completed_at")})

    return jsonify({"total": total_earned, "this_period": this_period, "last_period": last_period, "by_month": by_month, "by_project": by_project}), 200


@freelancer_bp.route('/reviews', methods=['GET'])
@freelancer_required
def get_reviews(current_user):
    freelancer_id = str(current_user["_id"])
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = {"freelancer_id": freelancer_id, "status": "completed", "freelancer_rating": {"$ne": None}}
    total = mongo.db.projects.count_documents(query)

    reviews_cursor = mongo.db.projects.find(query).sort("completed_at", -1).skip((page - 1) * per_page).limit(per_page)
    reviews = []
    for p in reviews_cursor:
        client = mongo.db.users.find_one({"_id": ObjectId(p["client_id"])})
        reviews.append({
            "id": str(p["_id"]),
            "project_title": p.get("title"),
            "rating": p.get("freelancer_rating"),
            "comment": p.get("freelancer_review_comment", ""),
            "date": p.get("completed_at"),
            "client": {
                "full_name": client.get("full_name") if client else "Unknown",
                "avatar_initials": client.get("full_name", "?")[0].upper() if client and client.get("full_name") else "?"
            }
        })

    return jsonify({"reviews": reviews, "total": total, "page": page, "per_page": per_page}), 200


@freelancer_bp.route('/portfolio/projects', methods=['POST'])
@freelancer_required
def add_portfolio_project(current_user):
    user_id = str(current_user["_id"])
    profile = _get_profile(user_id)
    data = request.get_json() or {}

    title = str(data.get('title', '')).strip()
    description = str(data.get('description', '')).strip()
    if not title or not description:
        return jsonify({'error': 'title and description are required'}), 400

    project = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "category": str(data.get('category', 'Other')).strip(),
        "images": data.get('images', []) if isinstance(data.get('images'), list) else [],
        "technologies": data.get('technologies', []) if isinstance(data.get('technologies'), list) else [],
        "project_url": str(data.get('project_url', '')).strip(),
        "github_url": str(data.get('github_url', '')).strip(),
        "completed_date": data.get('completed_date'),
        "client_name": str(data.get('client_name', '')).strip(),
        "is_featured": bool(data.get('is_featured', False)),
        "created_at": datetime.datetime.now(datetime.timezone.utc),
    }

    projects = profile.get("portfolio_projects", [])
    projects.append(project)
    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"portfolio_projects": projects}})
    return jsonify({"project": project, "portfolio_projects": projects}), 201


@freelancer_bp.route('/portfolio/projects/<project_id>', methods=['PUT'])
@freelancer_required
def update_portfolio_project(current_user, project_id):
    user_id = str(current_user["_id"])
    profile = _get_profile(user_id)
    data = request.get_json() or {}

    projects = profile.get("portfolio_projects", [])
    idx, project = _find_project(projects, project_id)
    if idx < 0:
        return jsonify({'error': 'Project not found'}), 404

    for field in ["title", "description", "category", "images", "technologies", "project_url", "github_url", "completed_date", "client_name", "is_featured"]:
        if field in data:
            project[field] = data[field]

    projects[idx] = project
    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"portfolio_projects": projects}})
    return jsonify({"project": project, "portfolio_projects": projects}), 200


@freelancer_bp.route('/portfolio/projects/<project_id>', methods=['DELETE'])
@freelancer_required
def delete_portfolio_project(current_user, project_id):
    user_id = str(current_user["_id"])
    profile = _get_profile(user_id)
    projects = profile.get("portfolio_projects", [])
    next_projects = [p for p in projects if str(p.get("id")) != str(project_id)]
    if len(next_projects) == len(projects):
        return jsonify({'error': 'Project not found'}), 404

    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"portfolio_projects": next_projects}})
    return jsonify({"ok": True, "portfolio_projects": next_projects}), 200


@freelancer_bp.route('/portfolio/projects/<project_id>/feature', methods=['PATCH'])
@freelancer_required
def feature_portfolio_project(current_user, project_id):
    user_id = str(current_user["_id"])
    profile = _get_profile(user_id)
    projects = profile.get("portfolio_projects", [])
    idx, project = _find_project(projects, project_id)
    if idx < 0:
        return jsonify({'error': 'Project not found'}), 404

    project["is_featured"] = not bool(project.get("is_featured", False))
    projects[idx] = project
    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"portfolio_projects": projects}})
    return jsonify({"project": project}), 200


@freelancer_bp.route('/portfolio/projects/<project_id>/images', methods=['POST'])
@freelancer_required
def upload_portfolio_images(current_user, project_id):
    user_id = str(current_user["_id"])
    profile = _get_profile(user_id)
    projects = profile.get("portfolio_projects", [])
    idx, project = _find_project(projects, project_id)
    if idx < 0:
        return jsonify({'error': 'Project not found'}), 404

    files = request.files.getlist('images')
    if not files:
        return jsonify({'error': 'No image files provided'}), 400

    existing_images = project.get("images", [])
    if len(existing_images) >= 10:
        return jsonify({'error': 'Max 10 images allowed per project'}), 400

    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    projects_dir = os.path.join(upload_folder, 'projects', user_id, project_id)
    os.makedirs(projects_dir, exist_ok=True)

    uploaded = []
    for f in files:
        ext = os.path.splitext((f.filename or '').lower())[1]
        if ext not in ALLOWED_IMAGE_EXT:
            return jsonify({'error': f'Unsupported image format: {ext}'}), 400
        if f.content_length and f.content_length > (5 * 1024 * 1024):
            return jsonify({'error': 'Each image must be <= 5MB'}), 400
        if len(existing_images) + len(uploaded) >= 10:
            break

        file_name = secure_filename(f"{uuid.uuid4().hex}{ext}")
        file_path = os.path.join(projects_dir, file_name)
        f.save(file_path)
        rel_url = f"uploads/projects/{user_id}/{project_id}/{file_name}"
        uploaded.append(rel_url)

    project["images"] = existing_images + uploaded
    projects[idx] = project
    mongo.db.freelancer_profiles.update_one({"user_id": user_id}, {"$set": {"portfolio_projects": projects}})
    return jsonify({"images": project["images"], "uploaded": uploaded}), 200

