from flask import Blueprint, request, jsonify
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity
from bson import ObjectId
import datetime
import uuid

from app import mongo, serialize, serialize_list

projects_bp = Blueprint('projects', __name__, url_prefix='/api/projects')


def _auth_project_access(f):
    """Decorator: JWT required + verify user is client or freelancer on the project."""
    @wraps(f)
    @jwt_required()
    def decorated(project_id, *args, **kwargs):
        user_id = get_jwt_identity()
        try:
            project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
        except Exception:
            return jsonify({"error": "Invalid project ID"}), 400
        if not project:
            return jsonify({"error": "Project not found"}), 404
        if project.get("client_id") != user_id and project.get("freelancer_id") != user_id:
            return jsonify({"error": "Unauthorized"}), 403
        return f(project, user_id, *args, **kwargs)
    return decorated


def _recompute_progress(project_id):
    """Recompute progress_percent from tasks done / total tasks."""
    project = mongo.db.projects.find_one({"_id": ObjectId(project_id)})
    if not project:
        return
    tasks = project.get("tasks", [])
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    progress = round((done / total) * 100, 1) if total > 0 else 0
    mongo.db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"progress_percent": progress}}
    )
    return progress


def _require_client(project, user_id, action="perform this action"):
    """Guard to ensure only the project client can mutate planning/payment data."""
    if project.get("client_id") != user_id:
        return jsonify({"error": f"Only the client can {action}"}), 403
    return None


# ─── MILESTONES ──────────────────────────────────────────────────────

@projects_bp.route('/<project_id>/milestones', methods=['POST'])
@_auth_project_access
def create_milestone(project, user_id):
    """Create a new milestone on the project."""
    client_only_error = _require_client(project, user_id, "manage milestones")
    if client_only_error:
        return client_only_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    milestone = {
        "id": str(uuid.uuid4()),
        "title": title,
        "due_date": data.get("due_date"),
        "status": "pending",
        "deliverables": data.get("deliverables", []),
        "budget_allocated": float(data.get("budget_allocated", 0))
    }

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$push": {"milestones": milestone}}
    )

    return jsonify({"milestone": milestone}), 201


@projects_bp.route('/<project_id>/milestones/<mid>', methods=['PATCH'])
@_auth_project_access
def update_milestone(project, user_id, mid):
    """Update a milestone (status, title, due_date, etc.)."""
    client_only_error = _require_client(project, user_id, "manage milestones")
    if client_only_error:
        return client_only_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    milestones = project.get("milestones", [])
    found = False
    for m in milestones:
        if m.get("id") == mid:
            found = True
            if "status" in data and data["status"] in ("pending", "in_progress", "done"):
                m["status"] = data["status"]
            if "title" in data:
                m["title"] = data["title"]
            if "due_date" in data:
                m["due_date"] = data["due_date"]
            if "deliverables" in data:
                m["deliverables"] = data["deliverables"]
            if "budget_allocated" in data:
                m["budget_allocated"] = float(data["budget_allocated"])
            break

    if not found:
        return jsonify({"error": "Milestone not found"}), 404

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$set": {"milestones": milestones}}
    )

    updated = next((m for m in milestones if m["id"] == mid), None)
    return jsonify({"milestone": updated}), 200


# ─── TASKS ────────────────────────────────────────────────────────────

@projects_bp.route('/<project_id>/tasks', methods=['POST'])
@_auth_project_access
def create_task(project, user_id):
    """Create a new task on the project."""
    client_only_error = _require_client(project, user_id, "manage tasks")
    if client_only_error:
        return client_only_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    task = {
        "id": str(uuid.uuid4()),
        "milestone_id": data.get("milestone_id"),
        "title": title,
        "description": (data.get("description") or "").strip(),
        "assigned_to": data.get("assigned_to"),
        "status": "todo",
        "priority": data.get("priority", "medium"),
        "due_date": data.get("due_date"),
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    if task["priority"] not in ("low", "medium", "high"):
        task["priority"] = "medium"

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$push": {"tasks": task}}
    )

    progress = _recompute_progress(str(project["_id"]))
    return jsonify({"task": task, "progress_percent": progress}), 201


@projects_bp.route('/<project_id>/tasks/<tid>', methods=['PATCH'])
@_auth_project_access
def update_task(project, user_id, tid):
    """Update a task (status, priority, assignee, etc.)."""
    client_only_error = _require_client(project, user_id, "manage tasks")
    if client_only_error:
        return client_only_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    tasks = project.get("tasks", [])
    found = False
    for t in tasks:
        if t.get("id") == tid:
            found = True
            if "status" in data and data["status"] in ("todo", "in_progress", "review", "done"):
                t["status"] = data["status"]
            if "priority" in data and data["priority"] in ("low", "medium", "high"):
                t["priority"] = data["priority"]
            if "assigned_to" in data:
                t["assigned_to"] = data["assigned_to"]
            if "title" in data:
                t["title"] = data["title"]
            if "description" in data:
                t["description"] = data["description"]
            if "due_date" in data:
                t["due_date"] = data["due_date"]
            if "milestone_id" in data:
                t["milestone_id"] = data["milestone_id"]
            break

    if not found:
        return jsonify({"error": "Task not found"}), 404

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$set": {"tasks": tasks}}
    )

    progress = _recompute_progress(str(project["_id"]))
    updated = next((t for t in tasks if t["id"] == tid), None)
    return jsonify({"task": updated, "progress_percent": progress}), 200


@projects_bp.route('/<project_id>/tasks/<tid>', methods=['DELETE'])
@_auth_project_access
def delete_task(project, user_id, tid):
    """Delete a task from the project."""
    client_only_error = _require_client(project, user_id, "manage tasks")
    if client_only_error:
        return client_only_error

    tasks = project.get("tasks", [])
    new_tasks = [t for t in tasks if t.get("id") != tid]

    if len(new_tasks) == len(tasks):
        return jsonify({"error": "Task not found"}), 404

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$set": {"tasks": new_tasks}}
    )

    progress = _recompute_progress(str(project["_id"]))
    return jsonify({"message": "Task deleted", "progress_percent": progress}), 200


# ─── PROGRESS ─────────────────────────────────────────────────────────

@projects_bp.route('/<project_id>/progress', methods=['GET'])
@_auth_project_access
def get_progress(project, user_id):
    """Return progress_percent + milestone overview."""
    tasks = project.get("tasks", [])
    milestones = project.get("milestones", [])

    total_tasks = len(tasks)
    done_tasks = sum(1 for t in tasks if t.get("status") == "done")
    progress = round((done_tasks / total_tasks) * 100, 1) if total_tasks > 0 else 0

    milestone_overview = []
    for m in milestones:
        m_tasks = [t for t in tasks if t.get("milestone_id") == m.get("id")]
        m_done = sum(1 for t in m_tasks if t.get("status") == "done")
        milestone_overview.append({
            "id": m["id"],
            "title": m["title"],
            "status": m["status"],
            "due_date": m.get("due_date"),
            "total_tasks": len(m_tasks),
            "done_tasks": m_done,
            "budget_allocated": m.get("budget_allocated", 0)
        })

    return jsonify({
        "progress_percent": progress,
        "total_tasks": total_tasks,
        "done_tasks": done_tasks,
        "milestones": milestone_overview,
        "total_budget": project.get("total_budget", 0),
        "paid_amount": project.get("paid_amount", 0)
    }), 200


# ─── DELIVERABLES ─────────────────────────────────────────────────────

@projects_bp.route('/<project_id>/deliverables', methods=['POST'])
@_auth_project_access
def add_deliverable(project, user_id):
    """Upload/attach a deliverable file link to a milestone."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    milestone_id = data.get("milestone_id")
    file_url = (data.get("file_url") or "").strip()
    file_name = (data.get("file_name") or "").strip()

    if not file_url:
        return jsonify({"error": "file_url is required"}), 400

    deliverable = {
        "id": str(uuid.uuid4()),
        "milestone_id": milestone_id,
        "file_url": file_url,
        "file_name": file_name or file_url.split("/")[-1],
        "uploaded_by": user_id,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "confirmed": False
    }

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$push": {"deliverables_list": deliverable}}
    )

    return jsonify({"deliverable": deliverable}), 201


@projects_bp.route('/<project_id>/deliverables', methods=['GET'])
@_auth_project_access
def get_deliverables(project, user_id):
    """Return all deliverables for the project."""
    deliverables = project.get("deliverables_list", [])
    return jsonify({"deliverables": deliverables}), 200


@projects_bp.route('/<project_id>/deliverables/<did>/confirm', methods=['PATCH'])
@_auth_project_access
def confirm_deliverable(project, user_id, did):
    """Client confirms receipt of a deliverable."""
    if project.get("client_id") != user_id:
        return jsonify({"error": "Only the client can confirm deliverables"}), 403

    deliverables = project.get("deliverables_list", [])
    found = False
    for d in deliverables:
        if d.get("id") == did:
            d["confirmed"] = True
            d["confirmed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            found = True
            break

    if not found:
        return jsonify({"error": "Deliverable not found"}), 404

    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$set": {"deliverables_list": deliverables}}
    )

    return jsonify({"message": "Deliverable confirmed"}), 200


# ─── PROJECT DETAIL (full payload for the dashboard) ──────────────────

@projects_bp.route('/<project_id>/detail', methods=['GET'])
@_auth_project_access
def get_project_detail(project, user_id):
    """Return full project detail including milestones, tasks, budget, deliverables."""
    # Populate freelancer info
    freelancer = mongo.db.users.find_one({"_id": ObjectId(project["freelancer_id"])})
    if freelancer:
        prof = mongo.db.freelancer_profiles.find_one({"user_id": project["freelancer_id"]})
        project["freelancer"] = {
            "id": str(freelancer["_id"]),
            "full_name": freelancer.get("full_name"),
            "avatar_initials": freelancer.get("full_name", "?")[0].upper(),
            "rating": prof.get("avg_rating", 0) if prof else 0,
        }

    # Populate client info
    client = mongo.db.users.find_one({"_id": ObjectId(project["client_id"])})
    if client:
        project["client"] = {
            "id": str(client["_id"]),
            "full_name": client.get("full_name"),
            "avatar_initials": client.get("full_name", "?")[0].upper(),
        }

    # Recompute progress
    tasks = project.get("tasks", [])
    total = len(tasks)
    done = sum(1 for t in tasks if t.get("status") == "done")
    project["progress_percent"] = round((done / total) * 100, 1) if total > 0 else 0

    # Ensure fields exist
    project.setdefault("milestones", [])
    project.setdefault("tasks", [])
    project.setdefault("deliverables_list", [])
    project.setdefault("total_budget", 0)
    project.setdefault("paid_amount", 0)

    return jsonify({"project": serialize(project)}), 200


# ─── UPCOMING MILESTONES (cross-project) ──────────────────────────────

@projects_bp.route('/upcoming-milestones', methods=['GET'])
@jwt_required()
def upcoming_milestones():
    """Return next 3 upcoming milestones across all active projects for the user."""
    user_id = get_jwt_identity()
    active_projects = list(mongo.db.projects.find({
        "$or": [{"client_id": user_id}, {"freelancer_id": user_id}],
        "status": "active"
    }))

    upcoming = []
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    for p in active_projects:
        for m in p.get("milestones", []):
            if m.get("status") != "done" and m.get("due_date"):
                # Populate assignee info from freelancer
                assignee = None
                freelancer = mongo.db.users.find_one({"_id": ObjectId(p["freelancer_id"])})
                if freelancer:
                    assignee = {
                        "id": str(freelancer["_id"]),
                        "full_name": freelancer.get("full_name"),
                        "avatar_initials": freelancer.get("full_name", "?")[0].upper(),
                    }

                upcoming.append({
                    "milestone_id": m["id"],
                    "milestone_title": m["title"],
                    "due_date": m["due_date"],
                    "status": m["status"],
                    "project_id": str(p["_id"]),
                    "project_title": p.get("title", ""),
                    "assignee": assignee,
                })

    # Sort by due_date ascending, take top 3
    upcoming.sort(key=lambda x: x.get("due_date", ""))
    return jsonify({"milestones": upcoming[:3]}), 200


# ─── BUDGET UPDATE ────────────────────────────────────────────────────

@projects_bp.route('/<project_id>/budget', methods=['PATCH'])
@_auth_project_access
def update_budget(project, user_id, ):
    """Update total_budget or paid_amount."""
    client_only_error = _require_client(project, user_id, "update budget")
    if client_only_error:
        return client_only_error

    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400

    update = {}
    if "total_budget" in data:
        update["total_budget"] = float(data["total_budget"])
    if "paid_amount" in data:
        update["paid_amount"] = float(data["paid_amount"])

    if update:
        mongo.db.projects.update_one({"_id": project["_id"]}, {"$set": update})

    return jsonify({"message": "Budget updated", **update}), 200


@projects_bp.route('/<project_id>/complete', methods=['PATCH'])
@_auth_project_access
def complete_project(project, user_id):
    """Mark project as completed and require a client review note + rating."""
    client_only_error = _require_client(project, user_id, "complete and pay for the project")
    if client_only_error:
        return client_only_error

    data = request.get_json(silent=True) or {}
    paid_amount = data.get("paid_amount")
    rating = data.get("rating")
    comment = (data.get("comment") or "").strip()
    total_budget = float(project.get("total_budget", 0) or 0)

    if paid_amount is None:
        paid_amount = total_budget
    else:
        paid_amount = float(paid_amount)

    try:
        rating_int = int(rating)
    except (TypeError, ValueError):
        return jsonify({"error": "rating is required and must be an integer between 1 and 5"}), 400

    if rating_int < 1 or rating_int > 5:
        return jsonify({"error": "rating must be between 1 and 5"}), 400
    if not comment:
        return jsonify({"error": "review comment is required"}), 400

    if paid_amount < 0:
        return jsonify({"error": "paid_amount cannot be negative"}), 400
    if total_budget > 0 and paid_amount > total_budget:
        return jsonify({"error": "paid_amount cannot exceed total budget"}), 400

    existing_review = mongo.db.reviews.find_one({
        "project_id": str(project["_id"]),
        "reviewer_id": user_id
    })
    if existing_review:
        return jsonify({"error": "Review already submitted for this project"}), 400

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    mongo.db.projects.update_one(
        {"_id": project["_id"]},
        {"$set": {
            "status": "completed",
            "completed_at": now,
            "paid_amount": paid_amount,
            "freelancer_rating": rating_int,
            "freelancer_review": comment
        }}
    )

    review_doc = {
        "project_id": str(project["_id"]),
        "reviewer_id": user_id,
        "target_id": project.get("freelancer_id"),
        "rating": rating_int,
        "comment": comment,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    mongo.db.reviews.insert_one(review_doc)

    return jsonify({
        "message": "Project marked as completed and review submitted",
        "status": "completed",
        "completed_at": now,
        "paid_amount": paid_amount,
        "rating": rating_int,
        "comment": comment
    }), 200


@projects_bp.route('/<project_id>/status', methods=['PATCH'])
@_auth_project_access
def update_project_status(project, user_id):
    """Client can move project to cancelled or disputed with optional reason."""
    client_only_error = _require_client(project, user_id, "change project status")
    if client_only_error:
        return client_only_error

    current_status = (project.get("status") or "").lower()
    if current_status in ("completed", "cancelled"):
        return jsonify({"error": f"Cannot change status from {current_status}"}), 400

    data = request.get_json(silent=True) or {}
    new_status = (data.get("status") or "").strip().lower()
    reason = (data.get("reason") or "").strip()

    if new_status not in ("cancelled", "disputed"):
        return jsonify({"error": "status must be 'cancelled' or 'disputed'"}), 400
    if new_status == "disputed" and not reason:
        return jsonify({"error": "reason is required when setting disputed status"}), 400

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    update = {"status": new_status}

    if new_status == "cancelled":
        update["cancelled_at"] = now
        if reason:
            update["cancellation_reason"] = reason
    if new_status == "disputed":
        update["disputed_at"] = now
        update["dispute_reason"] = reason

    mongo.db.projects.update_one({"_id": project["_id"]}, {"$set": update})
    return jsonify({
        "message": f"Project marked as {new_status}",
        "status": new_status,
        "reason": reason,
        "updated_at": now
    }), 200
