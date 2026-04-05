# 🧠 API Client Design Notes (Senior Data Engineer Mindset)

## 📌 Objective
Design a reusable, scalable, and production-ready API client for ingestion pipelines.

---

## 🧩 Core Principles (Senior Mindset)

### 1. Separation of Concerns
- `_build_url()` → Handles endpoint and query params
- `_request()` → Handles HTTP communication
- `get_all_data()` → Handles pagination logic

👉 Never mix responsibilities.

---

### 2. Reusability
- Avoid hardcoding values
- Inject configuration via `__init__`
- Design client to be reusable across pipelines

---

### 3. Fail Fast Philosophy
- Always validate responses
- Use `response.raise_for_status()`
- Raise explicit exceptions

---

### 4. Observability
- Logging should NOT live inside the client
- Logging belongs to the pipeline/orchestrator layer

---

### 5. Scalability Thinking
- Design for pagination from day 1
- Do not assume pagination style
- Follow API contract (offset, page, cursor, etc.)

---

## ⚙️ Client Structure

```python
class PeruOpenDataClient:

    def __init__(...):
        ...

    def _build_url(...):
        ...

    def _request(...):
        ...

    def get_all_data(...):
        ...
```

---

## 🔧 Key Design Decisions

### Init Parameters
- `base_url`
- `dataset_id`
- `api_key` (optional)
- `timeout` (default)

### Session Usage
- Always use `requests.Session()`
- Improves performance and connection reuse

---

## 🔄 Pagination Strategies

### Offset-based
```python
offset += limit
```

### Cursor / Last ID
```python
last_id = records[-1]["id"]
```

### Next URL
```python
next_url = response["next"]
```

👉 Always inspect API before implementing

---

## 🚨 Common Mistakes

- Hardcoding URLs ❌
- No error handling ❌
- Mixing logic in one function ❌
- Ignoring pagination ❌
- Not inspecting API response ❌

---

## 🏗️ Pipeline Integration

```text
Lambda Handler
    ↓
run_pipeline()
    ↓
API Client
    ↓
Raw Data (S3)
```

👉 Client = data extraction only  
👉 Pipeline = orchestration + storage + logging  

---

## 📚 Recommended Learning

### API & HTTP
- REST API Design Best Practices
- HTTP Methods & Status Codes

### Python
- `requests` library
- `urllib.parse`

### System Design
- Designing Data-Intensive Applications (Martin Kleppmann)

### Data Engineering
- Designing Data Pipelines (O'Reilly)

---

## 🚀 Next Steps

- Add retries (exponential backoff)
- Add logging (pipeline level)
- Integrate with S3 ingestion
- Add schema validation

---

## 🧠 Final Thought

A senior engineer does not just make things work —  
they design systems that are:

- maintainable  
- scalable  
- observable  
- reusable  
