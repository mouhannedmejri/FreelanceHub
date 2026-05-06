from flask import Blueprint, request, jsonify
from app import mongo, serialize_list

freelancers_bp = Blueprint("freelancers", __name__, url_prefix="/api/freelancers")


@freelancers_bp.route("/search", methods=["GET"])
def search_freelancers():
    q = request.args.get("q", "").strip()
    skills = request.args.getlist("skills[]") or request.args.getlist("skills")
    category = request.args.get("category", "").strip()
    location = request.args.get("location", "").strip()
    availability = request.args.get("availability", "").strip()
    sort_by = request.args.get("sort_by", "rating").strip()
    min_rating = request.args.get("min_rating", default=0.0, type=float)
    max_price = request.args.get("max_price", type=float)
    limit = min(request.args.get("limit", default=12, type=int), 50)
    skip = max(request.args.get("skip", default=0, type=int), 0)

    match_conditions = {"role": "freelancer", "status": {"$ne": "banned"}}

    if category and category.lower() != "all":
        match_conditions["derived_category"] = {"$regex": f"^{category}$", "$options": "i"}
    if location:
        match_conditions["profile.location"] = {"$regex": location, "$options": "i"}
    if availability == "online":
        match_conditions["is_online"] = True
    if max_price is not None:
        match_conditions["profile.hourly_rate"] = {"$lte": max_price}
    if skills:
        match_conditions["profile.skills"] = {"$all": skills}
    if q:
        match_conditions["$or"] = [
            {"full_name": {"$regex": q, "$options": "i"}},
            {"profile.title": {"$regex": q, "$options": "i"}},
            {"profile.bio": {"$regex": q, "$options": "i"}},
            {"profile.skills": {"$elemMatch": {"$regex": q, "$options": "i"}}},
        ]

    now_expr = {"$dateSubtract": {"startDate": "$$NOW", "unit": "minute", "amount": 5}}

    pipeline = [
        {"$match": {"role": "freelancer"}},
        {
            "$lookup": {
                "from": "freelancer_profiles",
                "let": {"uid": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$user_id", "$$uid"]}}},
                ],
                "as": "profile",
            }
        },
        {"$unwind": {"path": "$profile", "preserveNullAndEmptyArrays": True}},
        {
            "$lookup": {
                "from": "reviews",
                "let": {"uid": {"$toString": "$_id"}},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$target_id", "$$uid"]}}},
                    {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}, "total_reviews": {"$sum": 1}}},
                ],
                "as": "rating_data",
            }
        },
        {
            "$addFields": {
                "rating_data": {"$ifNull": [{"$arrayElemAt": ["$rating_data", 0]}, {}]},
                "is_online": {"$gte": ["$last_login_at", now_expr]},
            }
        },
        {
            "$addFields": {
                "avg_rating": {"$ifNull": ["$rating_data.avg_rating", {"$ifNull": ["$profile.avg_rating", 0]}]},
                "total_reviews": {"$ifNull": ["$rating_data.total_reviews", {"$ifNull": ["$profile.total_reviews", 0]}]},
                "derived_category": {
                    "$switch": {
                        "branches": [
                            {
                                "case": {"$regexMatch": {"input": {"$ifNull": ["$profile.title", ""]}, "regex": "design", "options": "i"}},
                                "then": "Designers",
                            },
                            {
                                "case": {"$regexMatch": {"input": {"$ifNull": ["$profile.title", ""]}, "regex": "developer|engineer", "options": "i"}},
                                "then": "Developers",
                            },
                            {
                                "case": {"$regexMatch": {"input": {"$ifNull": ["$profile.title", ""]}, "regex": "writer|copy", "options": "i"}},
                                "then": "Writers",
                            },
                            {
                                "case": {"$regexMatch": {"input": {"$ifNull": ["$profile.title", ""]}, "regex": "market", "options": "i"}},
                                "then": "Marketers",
                            },
                        ],
                        "default": {"$ifNull": ["$profile.category", "Other"]},
                    }
                },
            }
        },
        {"$match": match_conditions},
        {"$match": {"avg_rating": {"$gte": min_rating}}},
    ]

    sort_stage = {"avg_rating": -1, "total_reviews": -1}
    if sort_by == "reviews":
        sort_stage = {"total_reviews": -1, "avg_rating": -1}
    elif sort_by == "price_asc":
        sort_stage = {"profile.hourly_rate": 1, "avg_rating": -1}
    elif sort_by == "recent_activity":
        sort_stage = {"last_login_at": -1}

    pipeline.extend(
        [
            {"$sort": sort_stage},
            {
                "$facet": {
                    "data": [
                        {"$skip": skip},
                        {"$limit": limit},
                        {
                            "$project": {
                                "_id": 1,
                                "full_name": 1,
                                "email": 1,
                                "role": 1,
                                "status": 1,
                                "last_login_at": 1,
                                "is_online": 1,
                                "is_verified": {"$ifNull": ["$is_approved", False]},
                                "avg_rating": 1,
                                "total_reviews": 1,
                                "profile": {
                                    "title": {"$ifNull": ["$profile.title", "Freelancer"]},
                                    "bio": {"$ifNull": ["$profile.bio", ""]},
                                    "skills": {"$ifNull": ["$profile.skills", []]},
                                    "hourly_rate": {"$ifNull": ["$profile.hourly_rate", 0]},
                                    "location": {"$ifNull": ["$profile.location", "Remote"]},
                                    "portfolio": {"$ifNull": ["$profile.portfolio", []]},
                                    "category": {"$ifNull": ["$derived_category", "Other"]},
                                },
                            }
                        },
                    ],
                    "meta": [{"$count": "total"}],
                    "suggestions": [
                        {"$limit": 6},
                        {
                            "$project": {
                                "_id": 0,
                                "text": "$full_name",
                            }
                        },
                    ],
                }
            },
        ]
    )

    result = list(mongo.db.users.aggregate(pipeline))
    payload = result[0] if result else {"data": [], "meta": [], "suggestions": []}
    total = payload["meta"][0]["total"] if payload.get("meta") else 0

    return jsonify(
        {
            "data": serialize_list(payload.get("data", [])),
            "meta": {
                "total": total,
                "limit": limit,
                "skip": skip,
                "has_more": (skip + limit) < total,
            },
            "suggestions": payload.get("suggestions", []),
        }
    ), 200
