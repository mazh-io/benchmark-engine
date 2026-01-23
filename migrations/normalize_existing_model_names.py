"""
Migration Script: Normalize Existing Model Names

This script updates all existing model names in the database to use the normalized format.

Usage:
    python migrations/normalize_existing_model_names.py
    
    # Dry run (preview changes without saving):
    python migrations/normalize_existing_model_names.py --dry-run
    
What it does:
    1. Fetches all models from the database
    2. Normalizes each model name
    3. Updates models where the normalized name differs from the current name
    4. Prevents duplicates by checking if normalized name already exists
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from database.db_connector import get_db_client
from utils.model_name_normalizer import normalize_model_name
from typing import Dict, List, Tuple


def get_all_models_with_details(db) -> List[Dict]:
    """Fetch all models from database with their details."""
    models = db.get_all_models()
    if not models:
        print("No models found in database.")
        return []
    return models


def analyze_normalization_changes(models: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Analyze which models need normalization.
    
    Returns:
        - needs_update: Models that will be updated
        - unchanged: Models already normalized
        - potential_conflicts: Models that would create duplicates
    """
    needs_update = []
    unchanged = []
    potential_conflicts = []
    
    # Track normalized names per provider to detect conflicts
    normalized_names_by_provider = {}
    
    for model in models:
        model_id = model['id']
        current_name = model['name']
        provider_id = model['provider_id']
        normalized_name = normalize_model_name(current_name)
        
        # Track provider-specific normalized names
        if provider_id not in normalized_names_by_provider:
            normalized_names_by_provider[provider_id] = {}
        
        if current_name == normalized_name:
            unchanged.append({
                'id': model_id,
                'name': current_name,
                'provider_id': provider_id,
                'status': 'already_normalized'
            })
        else:
            # Check if this normalized name already exists for this provider
            if normalized_name in normalized_names_by_provider[provider_id]:
                potential_conflicts.append({
                    'id': model_id,
                    'current_name': current_name,
                    'normalized_name': normalized_name,
                    'provider_id': provider_id,
                    'status': 'duplicate',
                    'conflicts_with': normalized_names_by_provider[provider_id][normalized_name]
                })
            else:
                needs_update.append({
                    'id': model_id,
                    'current_name': current_name,
                    'normalized_name': normalized_name,
                    'provider_id': provider_id
                })
                normalized_names_by_provider[provider_id][normalized_name] = model_id
    
    return needs_update, unchanged, potential_conflicts


def update_model_name(db, model_id: str, new_name: str) -> bool:
    """
    Update a model's name in the database.
    
    This is a direct database update since there's no built-in method for this.
    """
    try:
        # For Supabase
        if hasattr(db, 'supabase'):
            response = db.supabase.table("models").update({
                "name": new_name
            }).eq("id", model_id).execute()
            return True
        
        # For Local PostgreSQL
        elif hasattr(db, '_get_connection'):
            conn = db._get_connection()
            cur = conn.cursor()
            cur.execute(
                "UPDATE models SET name = %s WHERE id = %s",
                (new_name, model_id)
            )
            conn.commit()
            cur.close()
            conn.close()
            return True
        
        return False
        
    except Exception as e:
        print(f"❌ Error updating model {model_id}: {e}")
        return False


def print_summary(needs_update: List[Dict], unchanged: List[Dict], conflicts: List[Dict]):
    """Print a summary of the migration analysis."""
    print("\n" + "=" * 80)
    print("MIGRATION ANALYSIS SUMMARY")
    print("=" * 80)
    
    print(f"\n📊 Total Models: {len(needs_update) + len(unchanged) + len(conflicts)}")
    print(f"   ✅ Already Normalized: {len(unchanged)}")
    print(f"   🔄 Needs Update: {len(needs_update)}")
    print(f"   ⚠️  Potential Conflicts: {len(conflicts)}")
    
    if needs_update:
        print("\n" + "-" * 80)
        print("MODELS TO BE UPDATED:")
        print("-" * 80)
        for model in needs_update[:20]:  # Show first 20
            print(f"  • {model['current_name']}")
            print(f"    → {model['normalized_name']}")
            print()
        
        if len(needs_update) > 20:
            print(f"  ... and {len(needs_update) - 20} more models")
    
    if conflicts:
        print("\n" + "-" * 80)
        print("⚠️  POTENTIAL CONFLICTS (will be skipped):")
        print("-" * 80)
        print("These models would create duplicate names for the same provider.")
        print("Manual review recommended.")
        for conflict in conflicts:
            print(f"  • {conflict['current_name']}")
            print(f"    → {conflict['normalized_name']} (already exists)")
            print()


def run_migration(dry_run: bool = False):
    """
    Execute the migration.
    
    Args:
        dry_run: If True, only preview changes without saving
    """
    print("\n" + "=" * 80)
    print("MODEL NAME NORMALIZATION MIGRATION")
    print("=" * 80)
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No changes will be saved to database")
    else:
        print("\n⚠️  LIVE MODE - Changes will be saved to database")
    
    # Get database client
    print("\n📡 Connecting to database...")
    db = get_db_client()
    
    # Fetch all models
    print("📥 Fetching all models...")
    models = get_all_models_with_details(db)
    
    if not models:
        print("❌ No models found. Exiting.")
        return
    
    print(f"✅ Found {len(models)} models")
    
    # Analyze what needs to change
    print("\n🔍 Analyzing normalization changes...")
    needs_update, unchanged, conflicts = analyze_normalization_changes(models)
    
    # Print summary
    print_summary(needs_update, unchanged, conflicts)
    
    # Ask for confirmation if not dry run
    if not dry_run and needs_update:
        print("\n" + "=" * 80)
        response = input(f"\n⚠️  About to update {len(needs_update)} models. Continue? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print("❌ Migration cancelled.")
            return
        
        # Perform updates
        print("\n🔄 Updating models...")
        success_count = 0
        error_count = 0
        
        for model in needs_update:
            print(f"  Updating: {model['current_name']} → {model['normalized_name']}", end=" ")
            
            if update_model_name(db, model['id'], model['normalized_name']):
                print("✅")
                success_count += 1
            else:
                print("❌")
                error_count += 1
        
        print("\n" + "=" * 80)
        print("MIGRATION COMPLETE")
        print("=" * 80)
        print(f"✅ Successfully updated: {success_count} models")
        if error_count > 0:
            print(f"❌ Failed to update: {error_count} models")
        if conflicts:
            print(f"⚠️  Skipped (conflicts): {len(conflicts)} models")
    
    elif dry_run:
        print("\n" + "=" * 80)
        print("DRY RUN COMPLETE - No changes were made")
        print("=" * 80)
        print("\nTo apply these changes, run:")
        print("  python migrations/normalize_existing_model_names.py")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Migrate existing model names to normalized format"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without saving to database"
    )
    
    args = parser.parse_args()
    
    try:
        run_migration(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n❌ Migration cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
