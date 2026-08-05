# Echolore to Arkana: Final Architectural Handoff

This document serves as the permanent, final handoff from the Echolore data-engineering layer to the Arkana AI layer. Echolore is now officially frozen and archived. Arkana is the sole active repository. 

This guide contains everything an Arkana engineer needs to know about the database state, architectural boundaries, and operational assumptions inherited from Echolore, ensuring the Echolore repository never needs to be reopened.

---

## 1. The Architectural Boundary

The division of responsibility between the two repositories is absolute and final, as defined in Echolore's `README.md`:

- **Echolore (Archived):** Strictly a Data Engineering and ETL system. Its sole responsibility was to extract raw JSONL, clean, normalize, deduplicate, and load the canonical heritage records into PostgreSQL.
- **Arkana (Active):** Owns **all downstream AI operations**. This includes chunking (SemanticChunker), embeddings, Qdrant vector storage, Hybrid Retrieval, Cross-Encoder reranking, Prompt Engineering, FastAPI endpoints, and the frontend React UI.

> [!CAUTION]
> Any references to RAG, Qdrant, embeddings, or APIs within the Echolore codebase (such as `scripts/embedder.py` or `chunker.py`) are strictly **[LEGACY] historical context**. They must never be reused or ported into Arkana.

---

## 2. Table Ownership and Modification Boundaries

Arkana consumes the `arkana_backup_2026-07-25.sql` dump. Below are the strict ownership rules for the restored PostgreSQL tables.

### Canonical Tables (Read-Only for Arkana)
Arkana must **NEVER** INSERT, UPDATE, or DELETE structural records in these tables (with one specific column exception detailed in Section 3).
- `heritage_sites`: The single source of truth for all 21,289 canonical heritage records.
- `site_images`: The canonical mapping of 1,304 site assets.
- `ingestion_log`: Historical logs of the ETL process.

### Arkana-Owned Tables (Read/Write)
- `rag_chunks`: Arkana completely owns this table. The existing 765 rows are disposable artifacts of Echolore's deprecated structural chunker. Arkana is expected to wipe this table and rebuild it using its own `SemanticChunker`.

---

## 3. Column Responsibilities

While the `heritage_sites` table is generally read-only for Arkana, there is **one critical column Arkana is expected to update**:

- **`last_embedded` (timestamp)**: Arkana **MUST** update this column to `NOW()` only after a completely successful pipeline run for a site. This is the only way Arkana tracks its synchronization state.

**The Strict Transactional Flow (with Idempotency):**
```text
Generate Semantic Chunks
       ↓
DELETE previous rag_chunks (where site_id = target)
       ↓
INSERT new rag_chunks (PostgreSQL)
       ↓
DELETE previous Qdrant vectors (where site_id = target) 
       ↓
UPSERT new vectors into Qdrant
       ↓
[ ONLY AFTER COMPLETE SUCCESS ]
       ↓
UPDATE heritage_sites SET last_embedded = NOW()
```

> [!CAUTION]
> If Qdrant crashes after `rag_chunks` are inserted, you **MUST NOT** update `last_embedded`. If you update the timestamp prematurely, that site will never retry, leaving PostgreSQL and Qdrant permanently out of sync. `last_embedded` is the final step of the transaction.

**Columns Echolore Maintained (Do Not Modify):**
- `content_hash`: Automatically computed SHA256 of the core fields. Used by Echolore's `loader.py` to only bump `updated_at` if the canonical text actually changed.
- `updated_at`: The timestamp Echolore bumped whenever upstream data changed.
- `wikidata_qid`: The globally unique deduplication key. Do not modify.

---

## 4. Legacy Scripts (Do Not Use)

The following Echolore scripts are explicitly deprecated and should not influence Arkana's design:
- `scripts/embedder.py`: Echolore's legacy script for generating vectors and writing to Qdrant/PostgreSQL.
- `ingestion/utils/chunker.py`: Echolore's legacy regex-based (`==+`) structural chunker.

Arkana must use its own native AI implementations (`SemanticChunker`, `Embedder`, etc.) instead of attempting to adapt these legacy files.

---

## 5. Intentionally Preserved Incremental Mechanisms

Arkana must rely on Echolore's intentionally designed incremental synchronization loop:

1. **Change Detection:** Echolore (in the past) compared the incoming `content_hash` against the database. If it changed, Echolore updated the `description` or `report_text` and bumped the `updated_at` timestamp.
2. **Arkana's Trigger:** Arkana should routinely poll `heritage_sites` using the query logic: 
   `WHERE (last_embedded IS NULL OR updated_at > last_embedded)`
3. **Arkana's Completion:** Upon completing the chunking and embedding for those sites, Arkana executes:
   `UPDATE heritage_sites SET last_embedded = NOW() WHERE site_id = ANY(...);`

---

## 6. Expected Migration Procedure

When standing up Arkana for the first time using the Echolore dump, execute this exact migration sequence:

1. **Restore the Dump:** Restore `arkana_backup_2026-07-25.sql` into the Arkana PostgreSQL instance.
2. **Wipe Legacy Data (ONE-TIME BOOTSTRAP):** Arkana intentionally discards every legacy chunk and every legacy embedding generated by Echolore's structural chunker. Run `DELETE FROM rag_chunks;` to clear the 765 legacy structural chunks, and destroy any legacy Qdrant collections.
3. **Reset Synchronization State (ONE-TIME BOOTSTRAP):** Run `UPDATE heritage_sites SET last_embedded = NULL;` to ensure Arkana ignores any legacy timestamps.
4. **Initial Semantic Re-Index:** Run Arkana's `SemanticChunker` over the entire `heritage_sites` dataset. The first startup always performs a complete semantic re-index from the canonical PostgreSQL data, regardless of the existing contents of `rag_chunks` or Qdrant.
5. **Mark as Synchronized:** Ensure Arkana sets `last_embedded = NOW()` as it processes each batch.

> [!NOTE]
> **The Qdrant Bootstrap**
> The first semantic indexing pass is intentionally a full rebuild. The entire PostgreSQL dataset is treated as unindexed regardless of existing `rag_chunks` or vector entries. After this bootstrap completes successfully, PostgreSQL becomes the source of truth and Arkana permanently switches to incremental synchronization using `updated_at > last_embedded`. No further full rebuilds are expected unless explicitly requested by an administrator.

> [!IMPORTANT]
> The `DELETE FROM rag_chunks` and `UPDATE last_embedded = NULL` commands are strictly a **one-time bootstrap operation** for Arkana's Day 1 migration. Arkana must **never** repeat these resets again. Going forward, Arkana must permanently rely on the incremental synchronization (`updated_at > last_embedded`) loop. Resetting timestamps destroys the incremental state and forces a complete O(N) re-index.

---

## 7. Assumptions Made About Downstream Consumers

Echolore baked in several assumptions that Arkana must adhere to:

- **Source Text Priority:** Arkana's chunker must read from `report_text` first (which contains high-fidelity long-form reports like IGNCA), and fall back to `description` if `report_text` is NULL.
- **Deletions Are Not Handled:** Echolore does not implement soft deletes or hard deletes. If a site disappeared from Echolore's upstream sources, Echolore simply stopped updating it. Arkana must assume any site in `heritage_sites` is valid and active indefinitely.
- **Geographic Indexing:** Coordinates are strictly stored as PostGIS `Geography` types (`SRID=4326;POINT(lon lat)`). Arkana spatial queries must leverage PostGIS geography functions (e.g., `ST_DWithin`).
- **No Network Calls Required:** Echolore's database contains the fully normalized, merged, and enriched text. Arkana does not need to (and should not) make API calls to Wikipedia, Wikidata, or UNESCO to perform chunking and embedding. The canonical DB is self-sufficient.

---

## 8. Hidden Coupling and Caveats

- **Cascade Deletions:** The `rag_chunks` table has a foreign key constraint (`rag_chunks_site_id_fkey`) referencing `heritage_sites(site_id) ON DELETE CASCADE`. If an Arkana admin manually deletes a site from `heritage_sites`, the chunks will automatically drop from PostgreSQL (but the vectors in Qdrant will be orphaned unless Arkana handles the synchronization).
- **RAG Eligibility:** Although `heritage_schema.py` contains a helper method `is_rag_eligible()` checking for `description_quality = 'full'`, **this rule was never enforced by the ETL pipeline**. Verification of `scripts/embedder.py` proves the pipeline strictly executed:
  `WHERE (description IS NOT NULL OR report_text IS NOT NULL)`
  Arkana should follow the implementation, not the schema helper: any site with a non-null `report_text` or `description` is structurally intended to be processed by the embedder.
- **Idempotency is Expected:** Because Echolore might have crashed or been re-run, its loader was built to be purely idempotent. Arkana's embedding pipeline must also be idempotent—if it processes the same site twice, it should overwrite the existing `rag_chunks` and Qdrant points for that `site_id` rather than duplicating them.
