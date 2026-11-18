# Database schema

SQLite is initialized programmatically by `backend/database.py`. Foreign keys are enabled on each connection.

```mermaid
erDiagram
 USERS ||--o{ SLOTS : examiner_creates
 USERS ||--o{ BOOKINGS : student_makes
 COURSES ||--o{ EXAMINATIONS : contains
 EXAMINATIONS ||--o{ RUBRICS : defines
 EXAMINATIONS ||--o{ SLOTS : schedules
 SLOTS ||--o{ BOOKINGS : receives
 BOOKINGS ||--o| EVALUATIONS : evaluated_by
 EVALUATIONS ||--o{ EVALUATION_CRITERIA : scores
 RUBRICS ||--o{ EVALUATION_CRITERIA : criterion
 USERS ||--o{ NOTIFICATIONS : receives
 USERS ||--o{ EXPORT_JOBS : requests
 USERS ||--o{ AUDIT_LOGS : acts
```

Tables: `users`, `courses`, `examinations`, `rubrics`, `slots`, `bookings`, `evaluations`, `evaluation_criteria`, `notifications`, `export_jobs`, `audit_logs`. Historical courses/examinations are deactivated/closed rather than deleted when referenced.
