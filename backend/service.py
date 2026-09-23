from collections import Counter

from .models import Contractor, Recommendation, RecommendRequest, RecommendResponse
from .ranking import explain, rank_candidates


def normalize(value: str) -> str:
    return " ".join(value.casefold().split())


def includes(values: tuple[str, ...], target: str) -> bool:
    return normalize(target) in {normalize(value) for value in values}


def rejection_reasons(c: Contractor, q: RecommendRequest) -> list[str]:
    reasons = []
    if q.event_date in c.busy_dates:
        reasons.append("busy_date")
    if c.price_from_kzt > q.budget:
        reasons.append("over_budget")
    if not includes(c.event_formats, q.event_type):
        reasons.append("event_type")
    if q.language and not includes(c.languages, q.language):
        reasons.append("language")
    if q.duration is not None and c.max_hours is not None and q.duration > c.max_hours:
        reasons.append("duration")
    return reasons


REASON_LABELS = {
    "busy_date": "заняты на выбранную дату",
    "over_budget": "начальная цена выше бюджета",
    "event_type": "не работают с выбранным форматом",
    "language": "не указан нужный язык",
    "duration": "превышен лимит часов",
}


def recommend(profiles: tuple[Contractor, ...], q: RecommendRequest) -> RecommendResponse:
    candidates = [c for c in profiles if normalize(c.city) == normalize(q.city)
                  and includes(c.categories, q.category)]
    matches = []
    excluded: Counter[str] = Counter()
    for c in candidates:
        reasons = rejection_reasons(c, q)
        excluded.update(reasons)
        if not reasons:
            matches.append(c)
    results = [Recommendation(
        id=c.id, name=c.anon_name,
        category=next(v for v in c.categories if normalize(v) == normalize(q.category)),
        city=c.city, price=c.price_from_kzt, explanation=explain(c, q),
        synthetic=c.synthetic, city_imputed=c.city_imputed, price_imputed=c.price_imputed,
    ) for c in rank_candidates(matches, q)[:3]]
    if not candidates:
        status = "no_category_in_city"
        message = "В этом городе нет подрядчиков выбранной категории."
    elif not results:
        status = "no_matches"
        message = "Подрядчики этой категории есть, но ни один не соответствует всем условиям."
    else:
        status = "matches_found"
        message = f"Подходят {len(matches)}; показаны {len(results)}."
        if len(results) < 3:
            message += f" Меньше трёх: в городе всего {len(candidates)} профилей этой категории, условиям соответствуют {len(matches)}."
    if excluded and len(results) < 3:
        message += " Причины исключения: " + "; ".join(
            f"{REASON_LABELS[key]} — {count}" for key, count in excluded.items()
        ) + ". Один профиль может иметь несколько причин."
    return RecommendResponse(
        status=status, count=len(results), results=results, message=message,
        total_candidates=len(candidates), total_matches=len(matches),
        exclusion_counts=dict(excluded),
    )
