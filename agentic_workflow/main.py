"""
Main entry point for the Agentic AI RAG Workflow System.
Provides multiple interfaces for interacting with the ARGO data analysis system.
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, Optional
from datetime import datetime

# Add the repository root to the path so `agentic_workflow` resolves as a package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_workflow.core.workflow_engine import WorkflowEngine
from agentic_workflow.core.config import config
from agentic_workflow.ui.cli_interface import CLIInterface
from agentic_workflow.utils.logger import setup_logging as configure_logging

def setup_logging(log_level: str = "INFO"):
    """Set up console logging without writing request-bearing local files."""
    configure_logging(log_level)

def print_system_info():
    """Print system information and status."""
    print("🌊 Agentic AI ARGO Data Explorer")
    print("=" * 50)
    print(f"Version: 1.0.0")
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print()
    
    # Check system status
    try:
        engine = WorkflowEngine()
        status = engine.get_system_status()
        
        print("System Status:")
        print(f"  Overall: {'✅ Ready' if status['system_ready'] else '❌ Issues'}")
        
        for service, available in status['service_status'].items():
            icon = "✅" if available else "❌"
            print(f"  {service.capitalize()}: {icon}")
        
        if not status['system_ready']:
            print("\n⚠️  Warning: Some services are unavailable.")
            print("   Please ensure PostgreSQL, ChromaDB, and Ollama are running.")
        
    except Exception as e:
        print(f"❌ Failed to check system status: {e}")
    
    print()

def run_single_query(query: str, 
                    output_format: str = "text",
                    include_technical: bool = False,
                    session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run a single query and return results.
    
    Args:
        query: Natural language query
        output_format: Output format ('text', 'json')
        include_technical: Include technical details
        session_id: Optional session identifier
        
    Returns:
        Query results
    """
    try:
        engine = WorkflowEngine()
        
        result = engine.process_query(
            user_query=query,
            session_id=session_id,
            include_technical_details=include_technical
        )
        
        if output_format == "json":
            print(json.dumps(result, indent=2, default=str))
        else:
            # Text output
            if "error" in result:
                print(f"❌ Error: {result['error']}")
                if "detailed_error" in result:
                    print(f"Details: {result['detailed_error']}")
            else:
                print_text_results(result)
        
        return result
        
    except Exception as e:
        error_result = {"error": f"Failed to process query: {str(e)}"}
        if output_format == "json":
            print(json.dumps(error_result, indent=2))
        else:
            print(f"❌ Error: {error_result['error']}")
        return error_result

def print_text_results(result: Dict[str, Any]):
    """Print results in text format."""
    print("\n" + "="*60)
    print("📊 ANALYSIS RESULTS")
    print("="*60)
    
    # Main response
    main_response = result.get("main_response", "")
    if main_response:
        print(f"\n💡 Summary:")
        print(main_response)
    
    # Data summary
    data_summary = result.get("data_summary", {})
    if data_summary:
        print(f"\n📈 Data Summary:")
        for key, value in data_summary.items():
            print(f"  • {key.replace('_', ' ').title()}: {value}")
    
    # Visualizations
    visualizations = result.get("visualizations", [])
    if visualizations:
        print(f"\n📊 Visualizations: {len(visualizations)} generated")
    
    # Recommendations
    recommendations = result.get("recommendations", [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
    
    # Metadata
    metadata = result.get("workflow_metadata", {})
    if metadata:
        duration = metadata.get("duration_seconds", 0)
        print(f"\n⏱️  Completed in {duration:.2f} seconds")

def run_batch_queries(queries_file: str, output_file: Optional[str] = None):
    """
    Run multiple queries from a file.
    
    Args:
        queries_file: Path to file containing queries (one per line)
        output_file: Optional output file for results
    """
    try:
        with open(queries_file, 'r') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        if not queries:
            print("❌ No queries found in file")
            return
        
        print(f"📝 Processing {len(queries)} queries from {queries_file}")
        
        results = []
        engine = WorkflowEngine()
        
        for i, query in enumerate(queries, 1):
            print(f"\n[{i}/{len(queries)}] Processing: {query[:60]}...")
            
            try:
                result = engine.process_query(
                    user_query=query,
                    session_id=f"batch_{i}",
                    include_technical_details=False
                )
                results.append({
                    "query": query,
                    "result": result,
                    "success": "error" not in result
                })
                
            except Exception as e:
                results.append({
                    "query": query,
                    "result": {"error": str(e)},
                    "success": False
                })
        
        # Output results
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n✅ Results saved to {output_file}")
        else:
            # Print summary
            successful = sum(1 for r in results if r["success"])
            print(f"\n📊 Batch Summary:")
            print(f"  Total queries: {len(results)}")
            print(f"  Successful: {successful}")
            print(f"  Failed: {len(results) - successful}")
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Agentic AI ARGO Data Explorer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                                    # Interactive CLI mode
  python main.py --query "Temperature in Bay of Bengal"  # Single query
  python main.py --batch queries.txt               # Batch processing
  python main.py --info                           # System information
        """
    )
    
    # Mode selection
    parser.add_argument("--query", "-q", type=str, 
                       help="Single query to process")
    parser.add_argument("--batch", "-b", type=str,
                       help="File containing queries to process (one per line)")
    parser.add_argument("--interactive", "-i", action="store_true",
                       help="Run in interactive CLI mode (default)")
    parser.add_argument("--info", action="store_true",
                       help="Show system information and status")
    
    # Output options
    parser.add_argument("--output", "-o", type=str,
                       help="Output file for results (batch mode)")
    parser.add_argument("--format", "-f", choices=["text", "json"], default="text",
                       help="Output format (default: text)")
    parser.add_argument("--technical", "-t", action="store_true",
                       help="Include technical details in output")
    
    # System options
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                       default="INFO", help="Logging level")
    parser.add_argument("--session-id", type=str,
                       help="Custom session identifier")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    
    # Handle different modes
    if args.info:
        print_system_info()
        return
    
    elif args.query:
        # Single query mode
        run_single_query(
            query=args.query,
            output_format=args.format,
            include_technical=args.technical,
            session_id=args.session_id
        )
    
    elif args.batch:
        # Batch processing mode
        run_batch_queries(args.batch, args.output)
    
    else:
        # Interactive CLI mode (default)
        try:
            cli = CLIInterface()
            cli.run_interactive()
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"❌ CLI failed to start: {e}")
            sys.exit(1)

if __name__ == "__main__":
    main()
