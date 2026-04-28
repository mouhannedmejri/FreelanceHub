import datetime
from bson import ObjectId
from app import mongo

def get_admin_stats():
    now = datetime.datetime.now(datetime.timezone.utc)
    start_of_this_month = datetime.datetime(now.year, now.month, 1, tzinfo=datetime.timezone.utc)
    
    if now.month == 1:
        start_of_last_month = datetime.datetime(now.year - 1, 12, 1, tzinfo=datetime.timezone.utc)
    else:
        start_of_last_month = datetime.datetime(now.year, now.month - 1, 1, tzinfo=datetime.timezone.utc)
    
    total_users = mongo.db.users.count_documents({})
    freelancers_count = mongo.db.users.count_documents({"role": "freelancer"})
    clients_count = mongo.db.users.count_documents({"role": "client"})
    admins_count = mongo.db.users.count_documents({"role": "admin"})

    pending_approvals = mongo.db.approval_requests.count_documents({"status": "pending"})
    open_claims = mongo.db.claims.count_documents({"status": "open"})
    
    active_projects = mongo.db.projects.count_documents({"status": "active"})
    completed_projects = mongo.db.projects.count_documents({"status": "completed"})

    pipeline = [{"$match": {"status": "completed"}}, {"$group": {"_id": None, "total_revenue": {"$sum": "$budget"}}}]
    rev_res = list(mongo.db.projects.aggregate(pipeline))
    total_revenue = rev_res[0]["total_revenue"] if rev_res else 0

    new_users_this_month = mongo.db.users.count_documents({"created_at": {"$gte": start_of_this_month}})
    new_users_last_month = mongo.db.users.count_documents({"created_at": {"$gte": start_of_last_month, "$lt": start_of_this_month}})

    pipeline_this_month = [{"$match": {"status": "completed", "completed_at": {"$gte": start_of_this_month}}}, {"$group": {"_id": None, "rev": {"$sum": "$budget"}}}]
    res_tm = list(mongo.db.projects.aggregate(pipeline_this_month))
    revenue_this_month = res_tm[0]["rev"] if res_tm else 0

    pipeline_last_month = [{"$match": {"status": "completed", "completed_at": {"$gte": start_of_last_month, "$lt": start_of_this_month}}}, {"$group": {"_id": None, "rev": {"$sum": "$budget"}}}]
    res_lm = list(mongo.db.projects.aggregate(pipeline_last_month))
    revenue_last_month = res_lm[0]["rev"] if res_lm else 0
    
    # Recent activity
    recent_users = list(mongo.db.users.find({}, {"full_name": 1, "created_at": 1}).sort("created_at", -1).limit(5))
    recent_claims = list(mongo.db.claims.find({}, {"title": 1, "created_at": 1}).sort("created_at", -1).limit(5))
    recent_approvals = list(mongo.db.approval_requests.find({}, {"type": 1, "created_at": 1}).sort("created_at", -1).limit(5))
    
    activity = []
    for u in recent_users:
        activity.append({"type": "user", "desc": f"Nouvel utilisateur: {u.get('full_name')}", "date": u.get("created_at")})
    for c in recent_claims:
        activity.append({"type": "claim", "desc": f"Nouvelle réclamation: {c.get('title')}", "date": c.get("created_at")})
    for a in recent_approvals:
        activity.append({"type": "approval", "desc": f"Nouvelle demande d'approbation ({a.get('type')})", "date": a.get("created_at")})
    
    activity.sort(key=lambda x: x["date"], reverse=True)
    recent_activity = activity[:5]
    
    return {
        "total_users": total_users,
        "freelancers_count": freelancers_count,
        "clients_count": clients_count,
        "admins_count": admins_count,
        "pending_approvals": pending_approvals,
        "open_claims": open_claims,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_revenue": total_revenue,
        "new_users_this_month": new_users_this_month,
        "new_users_last_month": new_users_last_month,
        "revenue_this_month": revenue_this_month,
        "revenue_last_month": revenue_last_month,
        "recent_activity": recent_activity
    }

def get_client_stats(client_id):
    total_offers = mongo.db.offers.count_documents({"client_id": client_id})
    active_projects = mongo.db.projects.count_documents({"client_id": client_id, "status": "active"})
    completed_projects = mongo.db.projects.count_documents({"client_id": client_id, "status": "completed"})
    
    pipeline = [
        {"$match": {"client_id": client_id, "status": "completed"}},
        {"$group": {"_id": None, "total_spent": {"$sum": "$budget"}, "avg_rating": {"$avg": "$freelancer_rating"}}}
    ]
    res = list(mongo.db.projects.aggregate(pipeline))
    
    total_spent = res[0]["total_spent"] if res else 0
    avg_rating_given = res[0]["avg_rating"] if res and res[0]["avg_rating"] is not None else 0
    
    # pending proposals for client
    pending_proposals = 0
    offers = list(mongo.db.offers.find({"client_id": client_id}))
    for o in offers:
        pending_proposals += mongo.db.proposals.count_documents({"offer_id": str(o["_id"]), "status": "pending"})
        
    return {
        "total_offers_posted": total_offers,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_spent": total_spent,
        "avg_freelancer_rating_given": avg_rating_given,
        "pending_proposals": pending_proposals
    }

def get_freelancer_stats(freelancer_id):
    total_proposals = mongo.db.proposals.count_documents({"freelancer_id": freelancer_id})
    active_projects = mongo.db.projects.count_documents({"freelancer_id": freelancer_id, "status": "active"})
    completed_projects = mongo.db.projects.count_documents({"freelancer_id": freelancer_id, "status": "completed"})
    
    pipeline = [
        {"$match": {"freelancer_id": freelancer_id, "status": "completed"}},
        {"$group": {"_id": None, "total_earned": {"$sum": "$budget"}, "avg_rating": {"$avg": "$freelancer_rating"}}}
    ]
    res = list(mongo.db.projects.aggregate(pipeline))
    
    total_earned = res[0]["total_earned"] if res else 0
    avg_rating_received = res[0]["avg_rating"] if res and res[0]["avg_rating"] is not None else 0
    
    total_projects = active_projects + completed_projects
    success_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
    
    total_reviews = mongo.db.projects.count_documents({"freelancer_id": freelancer_id, "status": "completed", "freelancer_rating": {"$ne": None}})
    proposals_accepted = mongo.db.proposals.count_documents({"freelancer_id": freelancer_id, "status": "accepted"})
    
    prof = mongo.db.freelancer_profiles.find_one({"user_id": freelancer_id})
    profile_views = prof.get("views", 0) if prof else 0
    
    return {
        "proposals_sent": total_proposals,
        "proposals_accepted": proposals_accepted,
        "active_projects": active_projects,
        "completed_projects": completed_projects,
        "total_earned": total_earned,
        "avg_rating": avg_rating_received,
        "total_reviews": total_reviews,
        "success_rate": success_rate,
        "profile_views": profile_views
    }
