#!/usr/bin/env python3
"""
Benchmark Engine - Local Database Testing Suite

Professional testing framework that executes benchmarks and saves results
to local PostgreSQL database (via pg-admin) instead of Supabase.

This is the primary testing tool for development and local validation.

Author: Benchmark Team
Version: 2.0.0
Python: 3.9+

Phases:
    Phase 1: Architecture & Resilience (MVP providers)
    Phase 2: OpenAI-Compatible Integration (DeepSeek, Cerebras, etc.)
    Phase 3: Custom SDK Integration (Anthropic, Google)
    Phase 4: Model Updates & Expansions (New models)
    All Phases: Complete end-to-end test

Usage:
    python test_with_local_db.py                        # Test all phases
    python test_with_local_db.py --phase 1              # Test Phase 1 only
    python test_with_local_db.py --phase 2              # Test Phase 2 only
    python test_with_local_db.py --phase 3              # Test Phase 3 only
    python test_with_local_db.py --phase 4              # Test Phase 4 only
    python test_with_local_db.py --provider deepseek    # Test single provider
"""

import sys
import os
import time
import argparse
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.constants import PROVIDERS
from database.local_db_client import (
    create_run, 
    update_run_status, 
    get_or_create_provider, 
    get_or_create_model, 
    save_result, 
    save_run_error,
    get_recent_results
)


# ============================================================================
# CONSTANTS & CONFIGURATION
# ============================================================================

VERSION = "2.0.0"
TEST_PROMPT = "Explain artificial intelligence in one paragraph."


# ============================================================================
# COLOR FORMATTING
# ============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'


# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PhaseResult:
    """Results for a single phase."""
    phase_number: int
    phase_name: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    duration_seconds: float
    total_tokens: int
    total_cost_usd: float
    avg_latency_ms: float


# ============================================================================
# OUTPUT FORMATTING
# ============================================================================

class OutputFormatter:
    """Professional terminal output formatting."""
    
    @staticmethod
    def header(text: str, width: int = 80):
        """Print header."""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*width}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text:^{width}}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*width}{Colors.ENDC}\n")
    
    @staticmethod
    def phase_header(phase_num: int, phase_name: str, model_count: int):
        """Print phase header."""
        print(f"\n{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}PHASE {phase_num}: {phase_name}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}Models to test: {model_count}{Colors.ENDC}")
        print(f"{Colors.CYAN}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
    
    @staticmethod
    def success(text: str):
        """Print success message."""
        print(f"{Colors.GREEN} {text}{Colors.ENDC}")
    
    @staticmethod
    def error(text: str):
        """Print error message."""
        print(f"{Colors.RED} {text}{Colors.ENDC}")
    
    @staticmethod
    def warning(text: str):
        """Print warning message."""
        print(f"{Colors.YELLOW}  {text}{Colors.ENDC}")
    
    @staticmethod
    def info(text: str):
        """Print info message."""
        print(f"{Colors.CYAN}  {text}{Colors.ENDC}")
    
    @staticmethod
    def metric(name: str, value: Any, width: int = 25):
        """Print metric."""
        print(f"   {Colors.BOLD}{name:<{width}}{Colors.ENDC} {value}")
    
    @staticmethod
    def separator():
        """Print separator."""
        print(f"{Colors.DIM}{'─'*80}{Colors.ENDC}")


# ============================================================================
# PHASE ORGANIZATION
# ============================================================================

class PhaseOrganizer:
    """Organize providers into test phases."""
    
    PHASE_NAMES = {
        1: "Architecture & Resilience",
        2: "OpenAI Compatible",
        3: "Custom SDK",
        4: "Model Updates"
    }
    
    @staticmethod
    def group_by_phase() -> Dict[int, List[Tuple[str, callable, str]]]:
        """
        Group all providers by implementation phase.
        
        Returns:
            Dictionary mapping phase numbers to provider tuples
        """
        phases = {
            1: [],  # Architecture & Resilience
            2: [],  # OpenAI Compatible
            3: [],  # Custom SDK
            4: [],  # Model Updates
        }
        
        for provider_name, func, model in PROVIDERS:
            # Phase 2: OpenAI Compatible (New providers)
            if provider_name in ["deepseek", "cerebras", "mistral", "fireworks", "sambanova"]:
                phases[2].append((provider_name, func, model))
            
            # Phase 3: Custom SDK (Anthropic, Google)
            elif provider_name in ["anthropic", "google"]:
                phases[3].append((provider_name, func, model))
            
            # Phase 4: Model Updates (New models for existing providers)
            elif provider_name in ["openai", "groq", "together", "openrouter"]:
                # New models added in Phase 4
                if model in ["gpt-4o", "o1-preview", "llama-3.3-70b-versatile", 
                            "meta-llama/Llama-3.3-70B-Instruct-Turbo", "minimax/minimax-01"]:
                    phases[4].append((provider_name, func, model))
                # Original MVP models (Phase 1)
                else:
                    phases[1].append((provider_name, func, model))
        
        return phases
    
    @staticmethod
    def get_phase_name(phase_num: int) -> str:
        """Get phase name."""
        return PhaseOrganizer.PHASE_NAMES.get(phase_num, "Unknown Phase")


# ============================================================================
# RUN MANAGER
# ============================================================================

class LocalRunManager:
    """Professional run manager with database integration."""
    
    def __init__(self, run_name: str = "local-test-run"):
        """Initialize run manager."""
        self.run_name = run_name
        self.run_id = None
        self.start_time = None
        self.formatter = OutputFormatter()
        
        # Overall stats
        self.total_successful = 0
        self.total_failed = 0
        self.phase_results: List[PhaseResult] = []
        
        # Current phase stats
        self.phase_successful = 0
        self.phase_failed = 0
        self.phase_start_time = None
        self.phase_tokens = 0
        self.phase_cost = 0.0
        self.phase_latencies = []
        
        # Initialize run
        self._initialize_run()
    
    def _initialize_run(self):
        """Initialize database run."""
        self.formatter.header("🚀 LOCAL DATABASE TEST RUN")
        
        self.formatter.info(f"Test Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.formatter.info(f"Database: benchmark_engine_local")
        self.formatter.info(f"Run Name: {self.run_name}")
        
        # Create run in database
        self.run_id = create_run(self.run_name, "manual_test")
        
        if self.run_id:
            self.formatter.success(f"Run created in database: {self.run_id}")
            self.start_time = time.time()
        else:
            raise Exception("Failed to create run in database!")
    
    def start_phase(self, phase_num: int, phase_name: str, model_count: int):
        """Start a new phase."""
        self.formatter.phase_header(phase_num, phase_name, model_count)
        
        # Reset phase stats
        self.phase_successful = 0
        self.phase_failed = 0
        self.phase_start_time = time.time()
        self.phase_tokens = 0
        self.phase_cost = 0.0
        self.phase_latencies = []
    
    def process_provider(self, provider_name: str, model: str, func: callable):
        """Process single provider and save to database."""
        print(f"\n{Colors.BOLD}Testing: {provider_name} / {model}{Colors.ENDC}")
        self.formatter.separator()
        
        # Get or create provider and model IDs
        provider_id = get_or_create_provider(provider_name)
        model_id = get_or_create_model(model, provider_id) if provider_id else None
        
        try:
            # Call provider
            start = time.time()
            result = func(TEST_PROMPT, model)
            elapsed = time.time() - start
            
            if result.get("success"):
                # Save successful result
                save_result(
                    run_id=self.run_id,
                    provider_id=provider_id,
                    model_id=model_id,
                    provider=provider_name,
                    model=model,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    total_latency_ms=result.get("total_latency_ms", 0),
                    ttft_ms=result.get("ttft_ms"),
                    tps=result.get("tps"),
                    cost_usd=result.get("cost_usd", 0),
                    status_code=result.get("status_code"),
                    success=True,
                    response_text=result.get("response_text", "")[:500]
                )
                
                # Update stats
                self.phase_successful += 1
                self.total_successful += 1
                self.phase_tokens += result.get("input_tokens", 0) + result.get("output_tokens", 0)
                self.phase_cost += result.get("cost_usd", 0)
                if result.get("total_latency_ms", 0) > 0:
                    self.phase_latencies.append(result.get("total_latency_ms", 0))
                
                # Display results
                self.formatter.success(f"SUCCESS in {elapsed:.2f}s")
                print(f"\n{Colors.BOLD}   📊 Metrics:{Colors.ENDC}")
                self.formatter.metric("Tokens:", 
                    f"{result.get('input_tokens', 0)} in / {result.get('output_tokens', 0)} out")
                self.formatter.metric("Cost:", f"${result.get('cost_usd', 0):.6f}")
                self.formatter.metric("Latency:", f"{result.get('total_latency_ms', 0):.2f} ms")
                
                if result.get('ttft_ms'):
                    self.formatter.metric("TTFT:", f"{result.get('ttft_ms'):.2f} ms")
                if result.get('tps'):
                    self.formatter.metric("TPS:", f"{result.get('tps'):.2f} tok/s")
                
                self.formatter.metric("Status:", result.get('status_code', 'N/A'))
            
            else:
                # Save error
                save_run_error(
                    run_id=self.run_id,
                    provider_id=provider_id,
                    model_id=model_id,
                    provider=provider_name,
                    model=model,
                    error_type=result.get("error_type", "UNKNOWN"),
                    error_message=result.get("error_message", "No details"),
                    status_code=result.get("status_code")
                )
                
                self.phase_failed += 1
                self.total_failed += 1
                self.formatter.error(f"FAILED: {result.get('error_message', 'Unknown error')}")
        
        except Exception as e:
            # Save exception as error
            save_run_error(
                run_id=self.run_id,
                provider_id=provider_id,
                model_id=model_id,
                provider=provider_name,
                model=model,
                error_type="EXCEPTION",
                error_message=str(e),
                status_code=None
            )
            
            self.phase_failed += 1
            self.total_failed += 1
            self.formatter.error(f"EXCEPTION: {str(e)}")
    
    def finish_phase(self, phase_num: int, phase_name: str):
        """Finish current phase and display summary."""
        phase_elapsed = time.time() - self.phase_start_time if self.phase_start_time else 0
        total_tests = self.phase_successful + self.phase_failed
        avg_latency = sum(self.phase_latencies) / len(self.phase_latencies) if self.phase_latencies else 0
        
        # Store phase result
        phase_result = PhaseResult(
            phase_number=phase_num,
            phase_name=phase_name,
            total_tests=total_tests,
            successful_tests=self.phase_successful,
            failed_tests=self.phase_failed,
            duration_seconds=phase_elapsed,
            total_tokens=self.phase_tokens,
            total_cost_usd=self.phase_cost,
            avg_latency_ms=avg_latency
        )
        self.phase_results.append(phase_result)
        
        # Display phase summary
        print(f"\n{Colors.BOLD}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.CYAN}PHASE {phase_num} SUMMARY: {phase_name}{Colors.ENDC}")
        print(f"{Colors.BOLD}{'='*80}{Colors.ENDC}\n")
        
        print(f"{Colors.BOLD}📊 Test Results:{Colors.ENDC}")
        self.formatter.metric("Total Tests:", total_tests)
        success_rate = (self.phase_successful / total_tests * 100) if total_tests > 0 else 0
        self.formatter.metric("Successful:", f"{self.phase_successful} ({success_rate:.1f}%)")
        self.formatter.metric("Failed:", self.phase_failed)
        self.formatter.metric("Duration:", f"{phase_elapsed:.2f}s")
        
        if self.phase_successful > 0:
            print(f"\n{Colors.BOLD}📈 Aggregated Metrics:{Colors.ENDC}")
            self.formatter.metric("Total Tokens:", f"{self.phase_tokens:,}")
            self.formatter.metric("Total Cost:", f"${self.phase_cost:.6f}")
            self.formatter.metric("Avg Latency:", f"{avg_latency:.2f} ms")
        
        # Status indicator
        if self.phase_failed == 0:
            self.formatter.success(f"\n🎉 Phase {phase_num} - ALL TESTS PASSED!")
        elif self.phase_successful > 0:
            self.formatter.warning(f" Phase {phase_num} - PARTIAL SUCCESS ({self.phase_successful}/{total_tests} passed)")
        else:
            self.formatter.error(f" Phase {phase_num} - ALL TESTS FAILED")
        
        print()
    
    def finish(self):
        """Finish run and display final summary."""
        total_elapsed = time.time() - self.start_time if self.start_time else 0
        total_tests = self.total_successful + self.total_failed
        
        # Mark run as finished (sets finished_at timestamp)
        update_run_status(self.run_id)
        
        # Display final summary
        self.formatter.header(" FINAL RUN SUMMARY")
        
        print(f"{Colors.BOLD}🎯 Overall Results:{Colors.ENDC}")
        self.formatter.metric("Run ID:", self.run_id)
        self.formatter.metric("Total Tests:", total_tests)
        success_rate = (self.total_successful / total_tests * 100) if total_tests > 0 else 0
        self.formatter.metric("Successful:", f"{self.total_successful} ({success_rate:.1f}%)")
        self.formatter.metric("Failed:", self.total_failed)
        self.formatter.metric("Total Duration:", f"{total_elapsed:.2f}s")
        self.formatter.metric("Avg per Test:", f"{total_elapsed/total_tests:.2f}s" if total_tests > 0 else "0s")
        
        # Phase breakdown
        if self.phase_results:
            print(f"\n{Colors.BOLD} Phase Breakdown:{Colors.ENDC}")
            for phase in self.phase_results:
                status_icon = "" if phase.failed_tests == 0 else "⚠️" if phase.successful_tests > 0 else ""
                success_rate = (phase.successful_tests / phase.total_tests * 100) if phase.total_tests > 0 else 0
                print(f"   {status_icon} Phase {phase.phase_number} ({phase.phase_name}): "
                      f"{phase.successful_tests}/{phase.total_tests} ({success_rate:.1f}%) "
                      f"in {phase.duration_seconds:.2f}s")
        
        # Overall aggregated metrics
        if self.phase_results:
            total_tokens = sum(p.total_tokens for p in self.phase_results)
            total_cost = sum(p.total_cost_usd for p in self.phase_results)
            
            print(f"\n{Colors.BOLD}💰 Overall Cost Analysis:{Colors.ENDC}")
            self.formatter.metric("Total Tokens Processed:", f"{total_tokens:,}")
            self.formatter.metric("Total Cost:", f"${total_cost:.6f}")
            self.formatter.metric("Avg Cost per Test:", f"${total_cost/total_tests:.6f}" if total_tests > 0 else "$0")
        
        # Display recent results from database
        self._display_recent_results()
        
        # Success celebration
        print()
        if self.total_failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}{'🎉 ALL TESTS PASSED! 🎉':^80}{Colors.ENDC}")
            print(f"{Colors.GREEN}{Colors.BOLD}{'='*80}{Colors.ENDC}")
        elif self.total_successful > 0:
            self.formatter.warning(f"✅ Partial Success: {self.total_successful}/{total_tests} tests passed")
        else:
            self.formatter.error(" All tests failed - check configuration and API keys")
        
        # Final instructions
        print()
        self.formatter.info(f"Test Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.formatter.success(" Results saved to local database: benchmark_engine_local")
        print(f"\n{Colors.BOLD}    Check pg-admin:{Colors.ENDC}")
        print(f"   • Database: benchmark_engine_local")
        print(f"   • Tables: runs, results, run_errors, providers, models")
        print(f"   • Run ID: {self.run_id}")
    
    def _display_recent_results(self):
        """Display recent results from database."""
        print(f"\n{Colors.BOLD} Recent Results from Database (Top 5):{Colors.ENDC}")
        
        recent = get_recent_results(limit=5)
        if recent:
            for i, r in enumerate(recent, 1):
                total_tokens = r.get('input_tokens', 0) + r.get('output_tokens', 0)
                print(f"   {i}. {r.get('provider')}/{r.get('model')}: "
                      f"${r.get('cost_usd', 0):.6f}, "
                      f"{r.get('total_latency_ms', 0):.0f}ms, "
                      f"{total_tokens} tokens")
        else:
            self.formatter.warning("   No results found in database")


# ============================================================================
# TEST RUNNER
# ============================================================================

class TestRunner:
    """Main test execution engine."""
    
    def __init__(self):
        """Initialize test runner."""
        self.formatter = OutputFormatter()
        self.phase_organizer = PhaseOrganizer()
    
    def run_all_phases(self):
        """Execute tests for all phases sequentially."""
        run_manager = LocalRunManager("all-phases-test")
        
        phases = self.phase_organizer.group_by_phase()
        
        try:
            for phase_num in sorted(phases.keys()):
                providers = phases[phase_num]
                if not providers:
                    continue
                
                phase_name = self.phase_organizer.get_phase_name(phase_num)
                run_manager.start_phase(phase_num, phase_name, len(providers))
                
                for prov, func, model in providers:
                    run_manager.process_provider(prov, model, func)
                    time.sleep(0.5)
                
                run_manager.finish_phase(phase_num, phase_name)
                time.sleep(1)
            
            run_manager.finish()
        
        except KeyboardInterrupt:
            self.formatter.warning("  Test interrupted by user")
            run_manager.finish()
        
        except Exception as e:
            self.formatter.error(f" Fatal error: {str(e)}")
            if run_manager.run_id:
                update_run_status(run_manager.run_id)
    
    def run_single_phase(self, phase_num: int):
        """Execute tests for a single phase."""
        phases = self.phase_organizer.group_by_phase()
        providers = phases.get(phase_num, [])
        
        if not providers:
            self.formatter.error(f"No providers found in Phase {phase_num}")
            return
        
        phase_name = self.phase_organizer.get_phase_name(phase_num)
        run_manager = LocalRunManager(f"phase-{phase_num}-test")
        
        try:
            run_manager.start_phase(phase_num, phase_name, len(providers))
            
            for prov, func, model in providers:
                run_manager.process_provider(prov, model, func)
                time.sleep(0.5)
            
            run_manager.finish_phase(phase_num, phase_name)
            run_manager.finish()
        
        except KeyboardInterrupt:
            self.formatter.warning("  Test interrupted by user")
            run_manager.finish()
        
        except Exception as e:
            self.formatter.error(f" Fatal error: {str(e)}")
            if run_manager.run_id:
                update_run_status(run_manager.run_id)
    
    def run_single_provider(self, provider_name: str):
        """Execute tests for a single provider (all models)."""
        provider_models = [
            (prov, func, model) 
            for prov, func, model in PROVIDERS 
            if prov.lower() == provider_name.lower()
        ]
        
        if not provider_models:
            self.formatter.error(f"Provider '{provider_name}' not found!")
            self.formatter.info("\nAvailable providers:")
            seen = set()
            for prov, _, _ in PROVIDERS:
                if prov not in seen:
                    print(f"  - {prov}")
                    seen.add(prov)
            return
        
        run_manager = LocalRunManager(f"{provider_name}-test")
        
        try:
            run_manager.start_phase(0, f"Provider: {provider_name}", len(provider_models))
            
            for prov, func, model in provider_models:
                run_manager.process_provider(prov, model, func)
                time.sleep(0.5)
            
            run_manager.finish_phase(0, f"Provider: {provider_name}")
            run_manager.finish()
        
        except KeyboardInterrupt:
            self.formatter.warning("  Test interrupted by user")
            run_manager.finish()
        
        except Exception as e:
            self.formatter.error(f" Fatal error: {str(e)}")
            if run_manager.run_id:
                update_run_status(run_manager.run_id)


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Benchmark Engine - Local Database Testing Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_with_local_db.py                 # Test all phases (19 models)
  python test_with_local_db.py --phase 1       # Test Phase 1 only
  python test_with_local_db.py --phase 2       # Test Phase 2 only
  python test_with_local_db.py --provider deepseek  # Test DeepSeek only
  
Database:
  Results are saved to: benchmark_engine_local (PostgreSQL)
  View in pg-admin: localhost:5432
        """
    )
    
    parser.add_argument(
        "--phase", 
        type=int, 
        choices=[1, 2, 3, 4],
        help="Test specific phase only (1=Architecture, 2=OpenAI Compatible, 3=Custom SDK, 4=Model Updates)"
    )
    parser.add_argument(
        "--provider", 
        type=str, 
        help="Test specific provider only (e.g., deepseek, anthropic, google)"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Benchmark Engine Local Test Suite v{VERSION}"
    )
    
    args = parser.parse_args()
    
    # Initialize test runner
    runner = TestRunner()
    
    # Execute based on arguments
    if args.provider:
        runner.run_single_provider(args.provider)
    elif args.phase is not None:
        runner.run_single_phase(args.phase)
    else:
        runner.run_all_phases()


if __name__ == "__main__":
    main()
