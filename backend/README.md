# Python backend

FastAPI читает 66 профилей из `data/contractors.csv` при запуске. CSV скопирован из предоставленного датасета без изменений; HTML служит только примером интерфейса. Python 3.10+.

Из корня репозитория (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-dev.txt
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs. Проверка данных: `GET /health`.

```powershell
$body = @{
    city = 'Астана'
    event_date = '2026-10-15'
    event_type = 'свадьба'
    category = 'Ведущий'
    budget = 900000
    duration = 6
    language = 'казахский'
} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8000/recommend -Method Post -ContentType 'application/json; charset=utf-8' -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
```

Обязательные поля: `city`, `event_date`, `event_type`, `category`, `budget` (целое число ₸, не меньше нуля). `duration` — положительное число часов, `language` — необязательная строка. Неизвестные поля, пустые строки и даты вне 23.09–31.12.2026 возвращают 422: за пределами окна доступность неизвестна.

Город и элементы списков сравниваются без учёта регистра и лишних пробелов, по полному значению. Категории, форматы, языки и даты в CSV разделены `|`. Занятые подрядчики исключаются; цена и часы сравниваются включительно. Пустой `max_hours` означает услугу без привязки к времени присутствия, а не отсутствие данных. Цена — **от**, за мероприятие: API проверяет начальную цену, не обещает окончательную стоимость и не умножает её на часы.

Ответ содержит `status`, `count` (число возвращённых карточек), `results`, `message`, `total_candidates` (город + категория), `total_matches` (все прошедшие фильтры), `exclusion_counts`. Максимум три карточки; условия автоматически не ослабляются.

| status | Значение |
| --- | --- |
| `matches_found` | Есть подходящие профили |
| `no_category_in_city` | В городе нет такой категории |
| `no_matches` | Категория есть, но условия исключают все профили |

`exclusion_counts` считает каждую причину, поэтому сумма может превышать число исключённых профилей. Карточки сохраняют `synthetic`, `city_imputed`, `price_imputed`; объяснения отмечают эти особенности данных.

Демо-запросы через `/docs`:

```json
{"city":"Астана","event_date":"2026-10-15","event_type":"свадьба","category":"Ведущий","budget":900000,"duration":6,"language":"казахский"}
```
```json
{"city":"Алматы","event_date":"2026-10-15","event_type":"свадьба","category":"Флорист","budget":1000000}
```
```json
{"city":"Астана","event_date":"2026-10-15","event_type":"свадьба","category":"Ведущий","budget":0}
```

Повторите первый запрос с датой `2026-10-16`: Санджи Виндсмок занят и исчезает из результата.

## Подключение ranking

`service.py` выполняет hard filtering. В `ranking.py` напарник заменяет `rank_candidates(candidates, request)` и `explain(candidate, request)`. Доступны все поля профиля, включая `description`. Ranking должен возвращать только переданных кандидатов без дублей и обеспечивать одинаковый порядок при одинаковом запросе.

Текущий baseline сначала выбирает несинтетические профили, затем профили с меньшим количеством заполненных при подготовке полей, затем сортирует по ID. Это технический детерминированный порядок, не семантический ranking. Объяснения построены по проверенным полям; анализ `description` и персонализация остаются задачей напарника. Полный критерий ТЗ о непереставляемых объяснениях этим стартовым backend не реализован.

## Настройки и тесты

`CONTRACTORS_CSV` задаёт альтернативный путь CSV; после изменения данных нужен перезапуск. Неверный CSV останавливает запуск с причиной ошибки. `CORS_ORIGINS` — список адресов frontend через запятую (по умолчанию localhost и 127.0.0.1 на порту 5173).

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q
```

Для запуска без тестовых зависимостей достаточно `backend/requirements.txt`. База данных и ключи внешних API не нужны.

`requirements-lock.txt` фиксирует полный набор зависимостей, проверенный на Python 3.14.6: `python -m pip install -r backend/requirements-lock.txt`. Проверка: 20 тестов проходят; установленный Starlette предупреждает о будущем переходе TestClient с httpx на httpx2.
