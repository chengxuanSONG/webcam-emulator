# 📄 Database Schema: `recordings.db`

The application uses a single embedded SQLite database to store metadata of all recording sessions.

## 📌 Table: `sessions`

| Column Name | Type    | Description                          |
|-------------|---------|--------------------------------------|
| `id`        | INTEGER | Primary key, auto-incremented        |
| `subject_id`| TEXT    | ID of the subject (e.g., sub-01)     |
| `session_id`| TEXT    | Session label (e.g., ses-01)         |
| `timestamp` | TEXT    | Date-time when recording was saved   |
| `frame_count`| INTEGER| Number of frames in this session     |
| `file_base` | TEXT    | Base path (without extension) for saved files (e.g., `sub-01/ses-01/func/filename`) |

## 🔗 Relationships

- This version contains a **single table**, so no foreign keys.
- In future, `sessions` could be related to a `channels` or `annotations` table.

