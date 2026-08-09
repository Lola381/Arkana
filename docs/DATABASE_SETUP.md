# Arkana — AI Database Setup Guide

Because the Arkana AI database is over 200MB, it is **not** hosted on GitHub due to file size limits. 
If you are a new developer trying to run the Python AI Backend locally, you must manually obtain and restore the PostgreSQL and Qdrant databases.

---

## 1. Obtain the Database Files
Ask the project maintainer to share the latest database backups with you via Google Drive or a secure transfer. You will need two specific files:
1. **`utf8.sql`**: The massive PostgreSQL dump containing all 21,000+ heritage sites, their metadata, and PostGIS geographic coordinates.
2. **`qdrant_snapshot.snapshot`**: The Qdrant vector database snapshot containing the semantic chunk embeddings for the AI RAG system.

---

## 2. Restore PostgreSQL (PostGIS)

Ensure you have PostgreSQL 16+ installed, along with the PostGIS extension.

1. Open your terminal or command prompt.
2. Log in as the postgres user and create an empty database named `arkana_db`:
   ```bash
   psql -U postgres -c "CREATE DATABASE arkana_db;"
   ```
3. Enable the PostGIS extension on the new database:
   ```bash
   psql -U postgres -d arkana_db -c "CREATE EXTENSION postgis;"
   ```
4. Restore the `utf8.sql` dump into your database:
   ```bash
   psql -U postgres -d arkana_db < path/to/utf8.sql
   ```

---

## 3. Restore Qdrant (Vector Embeddings)

Ensure you have Qdrant running locally on port `6333` (via Docker or native executable).

1. Copy the downloaded `.snapshot` file into your local Qdrant `snapshots/arkana_corpus/` directory.
   *(If you are using Docker, you may need to map a volume to `/qdrant/snapshots`)*
2. Use the Qdrant REST API to trigger the recovery process. You can run this curl command in your terminal:

```bash
curl -X PUT "http://localhost:6333/collections/arkana_corpus/snapshots/recover" \
     -H "Content-Type: application/json" \
     -d '{"location": "file:///qdrant/snapshots/arkana_corpus/qdrant_snapshot.snapshot"}'
```

3. Wait a few moments for the vectors to load into RAM. You can verify it worked by checking the collection info:
```bash
curl http://localhost:6333/collections/arkana_corpus
```

---

## 4. Verify AI Backend
Once both databases are restored, navigate to the `ai/` folder, install your python dependencies, and launch the FastAPI server.
```bash
cd ai/ai/backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```
Your backend will now successfully connect to PostgreSQL and Qdrant!
