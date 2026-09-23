"""Replace these functions with the team's semantic ranking and explanations.

Input candidates already passed all hard filters. The baseline prioritizes
non-synthetic profiles with fewer imputed fields, breaking ties by stable ID.
This is a data-quality ordering, not a semantic relevance score.
"""

from .models import Contractor, RecommendRequest


def rank_candidates(
    candidates: list[Contractor], request: RecommendRequest
) -> list[Contractor]:
    return sorted(candidates, key=lambda c: (
        c.synthetic, int(c.city_imputed) + int(c.price_imputed), c.id
    ))


def explain(candidate: Contractor, request: RecommendRequest) -> str:
    details = [
        f"{candidate.anon_name}: {candidate.city}",
        f"формат «{request.event_type}» указан в профиле",
        f"на {request.event_date.isoformat()} нет брони в календаре",
        f"цена от {candidate.price_from_kzt:,} ₸ при бюджете {request.budget:,} ₸",
    ]
    if request.language:
        details.append(f"рабочий язык — {request.language}")
    if request.duration is not None:
        details.append(
            "услуга не привязана к часам присутствия"
            if candidate.max_hours is None else
            f"длительность {request.duration:g} ч укладывается в лимит {candidate.max_hours:g} ч"
        )
    notes = []
    if candidate.price_imputed:
        notes.append("цена заполнена при подготовке датасета")
    if candidate.city_imputed:
        notes.append("город заполнен при подготовке датасета")
    if candidate.synthetic:
        notes.append("профиль синтетический")
    return "; ".join(details) + "." + (" Примечание: " + "; ".join(notes) + "." if notes else "")
