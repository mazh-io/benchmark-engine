"""
Vercel Cron Function: Sync Models from Provider APIs

This function runs weekly to:
1. Fetch available models from all provider APIs
2. Register them in the database with active=false
3. Mark models from ACTIVE_MODELS config as active=true

Cron schedule: Every Sunday at 2 AM UTC
"""

from http.server import BaseHTTPRequestHandler
import sys
from pathlib import Path
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.provider_service import sync_models_to_database


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""
    
    def do_GET(self):
        """Handle GET requests (for cron trigger)."""
        try:
            print("="*80)
            print(" STARTING WEEKLY MODEL SYNC")
            print("="*80)
            
            # Run sync
            result = sync_models_to_database()
            
            # Prepare response
            if result["success"]:
                status_code = 200
                response_data = {
                    "success": True,
                    "message": "Models synced successfully",
                    "providers_synced": result["providers_synced"],
                    "models_discovered": result["models_discovered"],
                    "models_activated": result["models_activated"]
                }
                print("\n✅ Sync completed successfully!")
            else:
                status_code = 500
                response_data = {
                    "success": False,
                    "message": "Model sync failed",
                    "errors": result["errors"]
                }
                print("\n❌ Sync failed with errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
            
            # Send response
            self.send_response(status_code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, indent=2).encode())
            
        except Exception as e:
            print(f"❌ Error in sync_models handler: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {
                "success": False,
                "error": str(e)
            }
            self.wfile.write(json.dumps(error_response).encode())
