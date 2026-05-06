import datetime
from typing import Dict, List, Tuple

INTEREST_CATEGORY_MAP = {
    "Technology": ["Web Dev", "Mobile Dev", "Software Engineering", "DevOps"],
    "Design": ["UI/UX", "Graphic Design", "Logo Design", "Illustration"],
    "Content": ["Writing", "Translation", "Copywriting", "Proofreading"],
    "Marketing": ["SEO", "Social Media", "Email Marketing", "Advertising"],
    "Video": ["Editing", "Animation", "Production"],
    "Business": ["Consulting", "Data Entry", "Virtual Assistant"],
}


def _normalize_interest_tokens(interests: List[str]) -> List[str]:
    tokens = set()
    for interest in interests or []:
        if not interest:
            continue
        lowered = interest.strip().lower()
        tokens.add(lowered)
        for _, subcats in INTEREST_CATEGORY_MAP.items():
            for sub in subcats:
                if lowered == sub.lower() or lowered in sub.lower() or sub.lower() in lowered:
                    tokens.add(sub.lower())
    return list(tokens)


def _interest_score(offer: Dict, user_interest_tokens: List[str]) -> Tuple[float, str]:
    if not user_interest_tokens:
        return 0.25, "No saved interests yet"
    searchable = " ".join(
        [
            str(offer.get("category", "")),
            str(offer.get("title", "")),
            " ".join(offer.get("skills", []) if isinstance(offer.get("skills"), list) else []),
        ]
    ).lower()
    matches = [token for token in user_interest_tokens if token in searchable]
    if not matches:
        return 0.0, "General exploration recommendation"
    score = min(1.0, len(set(matches)) / 3)
    return score, f"Matches your interests: {', '.join(sorted(set(matches))[:3])}"


def _budget_score(offer: Dict, client_budget_avg: float) -> float:
    if client_budget_avg <= 0:
        return 0.5
    target_budget = float(offer.get("budget_max") or offer.get("budget_min") or 0)
    if target_budget <= 0:
        return 0.3
    ratio = abs(target_budget - client_budget_avg) / max(client_budget_avg, 1)
    return max(0.0, min(1.0, 1 - ratio))


def _recency_score(created_at) -> float:
    if not created_at:
        return 0.2
    now = datetime.datetime.now(datetime.timezone.utc)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=datetime.timezone.utc)
    age_days = max(0.0, (now - created_at).total_seconds() / 86400)
    return max(0.0, min(1.0, 1 - (age_days / 30)))


def _engagement_score(proposals_count: int) -> float:
    proposals_count = max(0, int(proposals_count or 0))
    return max(0.0, min(1.0, 1 - (proposals_count / 20)))


def score_offer_for_client(offer: Dict, interests: List[str], client_budget_avg: float) -> Dict:
    interest_match, reason = _interest_score(offer, _normalize_interest_tokens(interests))
    budget_fit = _budget_score(offer, client_budget_avg)
    recency = _recency_score(offer.get("created_at"))
    engagement = _engagement_score(offer.get("proposals_count", 0))

    total = (interest_match * 0.50) + (budget_fit * 0.20) + (recency * 0.20) + (engagement * 0.10)
    return {
        "score": round(total, 4),
        "why_recommended": reason,
        "score_breakdown": {
            "interest_match": round(interest_match, 4),
            "budget_fit": round(budget_fit, 4),
            "recency": round(recency, 4),
            "engagement": round(engagement, 4),
        },
    }


def score_freelancer_for_client(freelancer: Dict, interests: List[str]) -> Dict:
    interest_match, reason = _interest_score(
        {
            "category": freelancer.get("profile", {}).get("category", ""),
            "title": freelancer.get("profile", {}).get("title", ""),
            "skills": freelancer.get("profile", {}).get("skills", []),
        },
        _normalize_interest_tokens(interests),
    )
    rating = float(freelancer.get("avg_rating") or 0)
    rating_score = max(0.0, min(1.0, rating / 5))
    recency = _recency_score(freelancer.get("last_login_at"))
    availability = 1.0 if freelancer.get("is_online") else 0.4
    total = (interest_match * 0.50) + (rating_score * 0.20) + (recency * 0.20) + (availability * 0.10)
    return {
        "score": round(total, 4),
        "why_recommended": reason,
        "score_breakdown": {
            "interest_match": round(interest_match, 4),
            "rating": round(rating_score, 4),
            "recency": round(recency, 4),
            "availability": round(availability, 4),
        },
    }


def score_offer_for_freelancer(offer: Dict, freelancer_skills: List[str]) -> Dict:
    tokens = [s.lower() for s in freelancer_skills or [] if s]
    interest_match, reason = _interest_score(offer, tokens)
    recency = _recency_score(offer.get("created_at"))
    engagement = _engagement_score(offer.get("proposals_count", 0))
    budget_fit = 0.6
    total = (interest_match * 0.50) + (budget_fit * 0.20) + (recency * 0.20) + (engagement * 0.10)
    return {
        "score": round(total, 4),
        "why_recommended": reason,
        "score_breakdown": {
            "interest_match": round(interest_match, 4),
            "budget_fit": round(budget_fit, 4),
            "recency": round(recency, 4),
            "engagement": round(engagement, 4),
        },
    }
