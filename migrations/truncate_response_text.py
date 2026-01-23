"""
Migration Script: Truncate Existing response_text

This script updates all existing successful benchmark results to truncate their
response_text to 100 characters, reducing database bloat by ~98%.

Usage:
    python migrations/truncate_response_text.py
    
    # Dry run (preview savings):
    python migrations/truncate_response_text.py --dry-run
    
What it does:
    1. Finds all successful runs with response_text > 100 chars
    2. Truncates them to 100 chars + "..."
    3. Keeps full text for failed runs (success=false) for debugging
    4. Reports storage savings
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from database.db_connector import get_db_client


def analyze_response_text_storage(db) -> dict:
    """Analyze current response_text storage usage."""
    try:
        if hasattr(db, 'supabase'):
            # Supabase
            response = db.supabase.table("benchmark_results").select(
                "id, success, response_text"
            ).execute()
            results = response.data
        else:
            # Local PostgreSQL
            conn = db._get_connection()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, success, LENGTH(response_text) as text_length
                FROM benchmark_results
                WHERE response_text IS NOT NULL
            """)
            results = [
                {"id": row[0], "success": row[1], "text_length": row[2]}
                for row in cur.fetchall()
            ]
            cur.close()
            conn.close()
        
        stats = {
            "total_records": len(results),
            "successful_runs": 0,
            "failed_runs": 0,
            "needs_truncation": 0,
            "total_chars_before": 0,
            "total_chars_after": 0,
            "records_to_update": []
        }
        
        for record in results:
            success = record.get("success", True)
            text_length = record.get("text_length") or (
                len(record.get("response_text", "")) if hasattr(db, 'supabase') else 0
            )
            
            if success:
                stats["successful_runs"] += 1
                stats["total_chars_before"] += text_length
                
                if text_length > 100:
                    stats["needs_truncation"] += 1
                    stats["total_chars_after"] += 103  # 100 chars + "..."
                    stats["records_to_update"].append(record["id"])
                else:
                    stats["total_chars_after"] += text_length
            else:
                stats["failed_runs"] += 1
                stats["total_chars_before"] += text_length
                stats["total_chars_after"] += text_length
        
        # Calculate savings
        chars_saved = stats["total_chars_before"] - stats["total_chars_after"]
        stats["chars_saved"] = chars_saved
        stats["mb_saved"] = round(chars_saved / 1024 / 1024, 2)
        stats["percent_reduction"] = round(
            (chars_saved / stats["total_chars_before"] * 100) if stats["total_chars_before"] > 0 else 0,
            1
        )
        
        return stats
        
    except Exception as e:
        print(f"❌ Error analyzing storage: {e}")
        return None


def truncate_existing_response_text(db, record_ids: list) -> tuple:
    """Truncate response_text for specified records."""
    success_count = 0
    error_count = 0
    
    try:
        if hasattr(db, 'supabase'):
            # Supabase - batch update
            for record_id in record_ids:
                try:
                    # Fetch record
                    response = db.supabase.table("benchmark_results").select(
                        "response_text"
                    ).eq("id", record_id).execute()
                    
                    if response.data and response.data[0].get("response_text"):
                        full_text = response.data[0]["response_text"]
                        truncated_text = full_text[:100] + "..."
                        
                        # Update record
                        db.supabase.table("benchmark_results").update({
                            "response_text": truncated_text
                        }).eq("id", record_id).execute()
                        
                        success_count += 1
                except Exception as e:
                    print(f"  Error updating {record_id}: {e}")
                    error_count += 1
        else:
            # Local PostgreSQL - single query
            conn = db._get_connection()
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE benchmark_results
                SET response_text = LEFT(response_text, 100) || '...'
                WHERE id = ANY(%s)
                AND LENGTH(response_text) > 100
            """, (record_ids,))
            
            success_count = cur.rowcount
            conn.commit()
            cur.close()
            conn.close()
        
        return success_count, error_count
        
    except Exception as e:
        print(f"❌ Error during truncation: {e}")
        return success_count, error_count


def print_analysis_summary(stats: dict):
    """Print analysis summary."""
    print("\n" + "=" * 80)
    print("STORAGE ANALYSIS")
    print("=" * 80)
    
    print(f"\n📊 Total Records: {stats['total_records']}")
    print(f"   ✅ Successful runs: {stats['successful_runs']}")
    print(f"   ❌ Failed runs: {stats['failed_runs']}")
    print(f"   🔄 Need truncation: {stats['needs_truncation']}")
    
    print(f"\n💾 Storage Impact:")
    print(f"   Before: {stats['total_chars_before']:,} characters")
    print(f"   After:  {stats['total_chars_after']:,} characters")
    print(f"   Saved:  {stats['chars_saved']:,} characters ({stats['mb_saved']} MB)")
    print(f"   Reduction: {stats['percent_reduction']}%")
    
    if stats['needs_truncation'] > 0:
        print(f"\n📝 Sample of records to truncate (first 10):")
        for record_id in stats['records_to_update'][:10]:
            print(f"   • {record_id}")
        
        if len(stats['records_to_update']) > 10:
            print(f"   ... and {len(stats['records_to_update']) - 10} more")


def run_migration(dry_run: bool = False):
    """Execute the migration."""
    print("\n" + "=" * 80)
    print("RESPONSE_TEXT TRUNCATION MIGRATION")
    print("=" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be saved")
    else:
        print("\n⚠️  LIVE MODE - Will truncate response_text for successful runs")
    
    # Connect to database
    print("\n📡 Connecting to database...")
    db = get_db_client()
    
    # Analyze storage
    print("📥 Analyzing response_text storage...")
    stats = analyze_response_text_storage(db)
    
    if not stats:
        print("❌ Analysis failed. Exiting.")
        return
    
    # Print analysis
    print_analysis_summary(stats)
    
    if stats['needs_truncation'] == 0:
        print("\n✅ No records need truncation!")
        return
    
    # Perform truncation if not dry run
    if not dry_run:
        print("\n" + "=" * 80)
        response = input(
            f"\n⚠️  About to truncate {stats['needs_truncation']} records. "
            f"This will save ~{stats['mb_saved']} MB. Continue? (yes/no): "
        )
        
        if response.lower() not in ['yes', 'y']:
            print("❌ Migration cancelled.")
            return
        
        print("\n🔄 Truncating response_text...")
        success, errors = truncate_existing_response_text(db, stats['records_to_update'])
        
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully truncated: {success} records")
        if errors > 0:
            print(f"❌ Failed to truncate: {errors} records")
        print(f"💾 Storage saved: ~{stats['mb_saved']} MB")
    else:
        print("\n" + "=" * 80)
        print("DRY RUN COMPLETE - No changes were made")
        print("=" * 80)
        print(f"\nPotential savings: ~{stats['mb_saved']} MB ({stats['percent_reduction']}% reduction)")
        print("\nTo apply these changes, run:")
        print("  python migrations/truncate_response_text.py")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Truncate existing response_text to save storage"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview storage savings without making changes"
    )
    
    args = parser.parse_args()
    
    try:
        run_migration(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
