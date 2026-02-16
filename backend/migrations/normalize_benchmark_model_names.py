"""
Migration Script: Normalize Model Names in benchmark_results and run_errors

The normalize_model_name function was only applied in get_or_create_model()
(models table), but the legacy 'model' TEXT field in benchmark_results and
run_errors still contained raw, un-normalized names.

This script fixes all existing rows.

Usage:
    python migrations/normalize_benchmark_model_names.py
    python migrations/normalize_benchmark_model_names.py --dry-run
"""

import sys
from pathlib import Path

# Add project root and src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from database.db_connector import get_db_client
from utils.model_name_normalizer import normalize_model_name


def normalize_table(db, table_name: str, dry_run: bool = False) -> dict:
    """
    Normalize the 'model' text field in the given table.

    Returns:
        dict with counts: total, updated, skipped, errors
    """
    stats = {"total": 0, "updated": 0, "skipped": 0, "errors": 0}

    # ---- Fetch all rows that have a model field ----
    try:
        if hasattr(db, "supabase"):
            # Supabase limits to 1000 rows per request — paginate through all
            rows = []
            page_size = 1000
            offset = 0
            while True:
                response = (
                    db.supabase.table(table_name)
                    .select("id, model")
                    .not_.is_("model", "null")
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
                batch = response.data or []
                rows.extend(batch)
                if len(batch) < page_size:
                    break  # Last page
                offset += page_size
                print(f"    ... fetched {len(rows)} rows so far")
        else:
            conn = db._get_connection()
            cur = conn.cursor()
            cur.execute(f"SELECT id, model FROM {table_name} WHERE model IS NOT NULL")
            rows = [{"id": r[0], "model": r[1]} for r in cur.fetchall()]
            cur.close()
            conn.close()
    except Exception as e:
        print(f"  ❌ Failed to read {table_name}: {e}")
        return stats

    stats["total"] = len(rows)
    print(f"  Found {len(rows)} rows with a model name")

    # ---- Check each row ----
    updates = []  # (id, old_name, new_name)
    for row in rows:
        row_id = str(row["id"])
        old_name = row["model"]
        new_name = normalize_model_name(old_name)

        if old_name == new_name:
            stats["skipped"] += 1
        else:
            updates.append((row_id, old_name, new_name))

    if not updates:
        print("  ✅ All rows already normalized")
        return stats

    print(f"  🔄 {len(updates)} rows need updating:")
    for row_id, old, new in updates[:15]:
        print(f"     {old}  →  {new}")
    if len(updates) > 15:
        print(f"     ... and {len(updates) - 15} more")

    if dry_run:
        stats["updated"] = len(updates)
        return stats

    # ---- Apply updates ----
    # Group by (old_name → new_name) to do bulk updates instead of row-by-row
    from collections import defaultdict
    groups = defaultdict(list)  # new_name → [old_names that map to it]
    old_to_new = {}
    for row_id, old_name, new_name in updates:
        old_to_new[old_name] = new_name
    unique_mappings = set((old, new) for old, new in old_to_new.items())

    print(f"  ⚡ Optimized: {len(unique_mappings)} unique name transformations (batch UPDATE)")

    for old_name, new_name in unique_mappings:
        try:
            if hasattr(db, "supabase"):
                # Batch: UPDATE ... SET model = new WHERE model = old
                db.supabase.table(table_name).update(
                    {"model": new_name}
                ).eq("model", old_name).execute()
            else:
                conn = db._get_connection()
                cur = conn.cursor()
                cur.execute(
                    f"UPDATE {table_name} SET model = %s WHERE model = %s",
                    (new_name, old_name),
                )
                conn.commit()
                cur.close()
                conn.close()

            # Count how many rows this affected
            affected = sum(1 for _, o, _ in updates if o == old_name)
            stats["updated"] += affected
            print(f"    ✅ {old_name} → {new_name}  ({affected} rows)")
        except Exception as e:
            affected = sum(1 for _, o, _ in updates if o == old_name)
            stats["errors"] += affected
            print(f"    ❌ {old_name} → {new_name}: {e}")

    return stats


def run_migration(dry_run: bool = False):
    mode = "DRY RUN" if dry_run else "LIVE"
    print("\n" + "=" * 70)
    print(f" NORMALIZE MODEL NAMES IN benchmark_results & run_errors  [{mode}]")
    print("=" * 70)

    db = get_db_client()

    for table in ("benchmark_results", "run_errors"):
        print(f"\n📋 Table: {table}")
        stats = normalize_table(db, table, dry_run=dry_run)
        print(f"  📊 Total={stats['total']}  Updated={stats['updated']}  "
              f"Skipped={stats['skipped']}  Errors={stats['errors']}")

    if dry_run:
        print("\n" + "=" * 70)
        print(" DRY RUN COMPLETE – no changes were written")
        print(" Run without --dry-run to apply changes.")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print(" ✅ MIGRATION COMPLETE")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Normalize the legacy 'model' text field in benchmark_results and run_errors"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    args = parser.parse_args()

    try:
        run_migration(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n❌ Cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
