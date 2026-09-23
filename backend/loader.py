import csv
from pathlib import Path

from .models import Contractor

DEFAULT_DATA_PATH = Path(__file__).resolve().parent / "data" / "contractors.csv"
REQUIRED_COLUMNS = set(Contractor.model_fields)


def load_contractors(path: Path = DEFAULT_DATA_PATH) -> tuple[Contractor, ...]:
    profiles = []
    ids = set()
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV missing columns: {', '.join(sorted(missing))}")
        for line, row in enumerate(reader, start=2):
            try:
                data = {key: row[key] for key in REQUIRED_COLUMNS}
                for key in ("categories", "event_formats", "languages", "busy_dates"):
                    data[key] = tuple(s.strip() for s in data[key].split("|") if s.strip())
                data["max_hours"] = data["max_hours"].strip() or None
                profile = Contractor.model_validate(data)
                if profile.id in ids:
                    raise ValueError(f"Duplicate contractor ID: {profile.id}")
                ids.add(profile.id)
                profiles.append(profile)
            except (ValueError, TypeError, AttributeError) as exc:
                raise ValueError(f"Invalid CSV record {line}: {exc}") from exc
    if not profiles:
        raise ValueError("CSV contains no contractor profiles")
    return tuple(profiles)
