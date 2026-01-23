"""
Queue-based Benchmark Runner

Processes benchmarks from a queue to avoid timeout issues.
Each invocation processes a batch of items from the queue.
"""

from database.db_connector import get_db_client
from utils.constants import BENCHMARK_PROMPT, PROVIDER_CONFIG
from utils.provider_service import get_providers
from typing import Optional

def run_benchmark_batch(batch_size: int = 5) -> dict:
    """
    Process a batch of benchmarks from the queue.
    
    Args:
        batch_size: Number of queue items to process in this batch
        
    Returns:
        Dictionary with processing statistics
    """
    db = get_db_client()
    
    # Get pending queue items
    queue_items = db.get_pending_queue_items(limit=batch_size)
    
    if not queue_items:
        print("No pending queue items found")
        return {
            "status": "idle",
            "processed": 0,
            "successful": 0,
            "failed": 0
        }
    
    print(f"Processing {len(queue_items)} queue items")
    
    processed = 0
    successful = 0
    failed = 0
    
    for item in queue_items:
        queue_id = str(item['id'])
        run_id = str(item['run_id'])
        provider_key = item['provider_key']
        model_name = item['model_name']
        
        print(f"\n{'='*60}")
        print(f"Queue Item {queue_id[:8]}... → {provider_key} / {model_name}")
        print(f"{'='*60}")
        
        # Mark as processing
        db.mark_queue_item_processing(queue_id)
        
        # Initialize variables for exception handler
        provider_id = None
        model_id = None
        
        try:
            # Get provider config
            provider_config = PROVIDER_CONFIG.get(provider_key, {
                "display_name": provider_key.title(), 
                "base_url": None
            })
            
            # Get or create provider in database
            provider_id = db.get_or_create_provider(
                name=provider_config.get("display_name", provider_key.title()),
                base_url=provider_config.get("base_url"),
                logo_url=None
            )
            
            # Get or create model
            if provider_id:
                model_id = db.get_or_create_model(
                    model_name=model_name,
                    provider_id=provider_id,
                    context_window=None
                )
            
            # Load and call provider function
            from utils.provider_service import get_provider_service
            provider_service = get_provider_service()
            provider_function = provider_service.get_provider_function(provider_key)
            
            # Call the provider
            result = provider_function(BENCHMARK_PROMPT, model_name)
            
            # Check if successful
            if not result.get("success", False):
                error_msg = result.get("error_message", "Unknown error")
                print(f"❌ Failed: {error_msg}")
                
                # Save error to run_errors table
                db.save_run_error(
                    run_id=run_id,
                    provider=provider_key,
                    model=model_name,
                    error_type=result.get("error_type", "UNKNOWN_ERROR"),
                    error_message=error_msg,
                    status_code=result.get("status_code"),
                    provider_id=provider_id,
                    model_id=model_id
                )
                
                # Mark queue item as failed
                db.mark_queue_item_failed(queue_id, error_msg)
                failed += 1
                processed += 1
                continue
            
            # Save successful result
            benchmark_data = {
                "run_id": run_id,
                "provider_id": provider_id,
                "model_id": model_id,
                "provider": provider_key,
                "model": model_name,
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "total_latency_ms": result.get("total_latency_ms") or result.get("latency_ms", 0),
                "ttft_ms": result.get("ttft_ms"),
                "tps": result.get("tps"),
                "status_code": result.get("status_code"),
                "cost_usd": result["cost_usd"],
                "success": result["success"],
                "error_message": result.get("error_message"),
                "response_text": result.get("response_text")
            }
            
            # Remove None values (except nullable fields)
            filtered_data = {}
            for k, v in benchmark_data.items():
                if k in ["provider_id", "model_id"]:
                    filtered_data[k] = v
                elif v is not None:
                    filtered_data[k] = v
            
            save_result = db.save_benchmark(**filtered_data)
            
            if save_result:
                print(f"✅ Success ({provider_key})")
                latency = result.get("total_latency_ms") or result.get("latency_ms", 0)
                print(f"   Latency: {latency:.2f} ms")
                if result.get("ttft_ms"):
                    print(f"   TTFT: {result['ttft_ms']:.2f} ms")
                if result.get("tps"):
                    print(f"   TPS: {result['tps']:.2f} tokens/sec")
                print(f"   Tokens: {result['input_tokens']} in / {result['output_tokens']} out")
                print(f"   Cost: ${result['cost_usd']:.6f}")
                
                # Mark queue item as completed
                db.mark_queue_item_completed(queue_id)
                successful += 1
            else:
                print(f"⚠️  DB save failed")
                db.mark_queue_item_failed(queue_id, "Failed to save to database")
                failed += 1
            
            processed += 1
            
        except Exception as e:
            error_msg = f"Exception during benchmark: {str(e)}"
            print(f"❌ CRITICAL ERROR: {error_msg}")
            
            # Save error (use try-except to ensure we always update queue status)
            try:
                db.save_run_error(
                    run_id=run_id,
                    provider=provider_key,
                    model=model_name,
                    error_type="PROVIDER_CRASH",
                    error_message=error_msg,
                    status_code=None,
                    provider_id=provider_id,
                    model_id=model_id
                )
            except Exception as save_error:
                print(f"⚠️  Failed to save error: {save_error}")
            
            # Always mark queue item as failed
            try:
                db.mark_queue_item_failed(queue_id, error_msg)
            except Exception as mark_error:
                print(f"⚠️  Failed to mark queue item as failed: {mark_error}")
            
            failed += 1
            processed += 1
    
    print(f"\n{'='*60}")
    print(f"Batch Complete: {processed} processed, {successful} successful, {failed} failed")
    print(f"{'='*60}")
    
    return {
        "status": "completed",
        "processed": processed,
        "successful": successful,
        "failed": failed
    }


def init_benchmark_queue(run_name: str = "queue-run", triggered_by: str = "system") -> Optional[str]:
    """
    Initialize a new benchmark run and populate the queue.
    
    Args:
        run_name: Name for the run
        triggered_by: Who triggered the run
        
    Returns:
        run_id of the created run, or None if failed
    """
    db = get_db_client()
    
    # Create run
    from benchmarking.run_manager import RunManager
    run_manager = RunManager(run_name, triggered_by)
    run_manager.start()
    
    if not run_manager.run_id:
        print("ERROR: Could not create run")
        return None
    
    print(f"Created run: {run_manager.run_id}")
    
    # Get all providers and models
    all_providers = get_providers()
    provider_models = [(prov, model) for prov, func, model in all_providers]
    
    # Enqueue all benchmarks
    success = db.enqueue_benchmarks(run_manager.run_id, provider_models)
    
    if success:
        print(f"Enqueued {len(provider_models)} benchmarks")
        return run_manager.run_id
    else:
        print("ERROR: Failed to enqueue benchmarks")
        return None
