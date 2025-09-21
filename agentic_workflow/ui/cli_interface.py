"""
Command Line Interface for the Agentic AI RAG Workflow System.
Provides interactive CLI for querying ARGO float data.
"""

import sys
import os
import argparse
import json
from typing import Dict, Any, Optional
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.workflow_engine import WorkflowEngine
from core.config import config

class CLIInterface:
    """Command line interface for the agentic workflow system."""
    
    def __init__(self):
        self.workflow_engine = WorkflowEngine()
        self.session_id = f"cli_session_{int(datetime.now().timestamp())}"
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for CLI interface."""
        # Reduce log noise for CLI
        logging.getLogger().setLevel(logging.WARNING)
        
        # Create CLI-specific logger
        self.logger = logging.getLogger("CLI")
        self.logger.setLevel(logging.INFO)
        
        # Add console handler for CLI messages
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def print_banner(self):
        """Print welcome banner."""
        banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    🌊 Agentic AI ARGO Data Explorer 🌊                      ║
║                                                                              ║
║  An intelligent system for analyzing oceanographic data from ARGO floats    ║
║  Ask questions in natural language about temperature, salinity, and more!   ║
╚══════════════════════════════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def print_help(self):
        """Print help information."""
        help_text = """
Available Commands:
  • Type your question in natural language
  • 'help' or '?' - Show this help message
  • 'status' - Check system status
  • 'history' - Show recent query history
  • 'examples' - Show example queries
  • 'clear' - Clear screen
  • 'quit' or 'exit' - Exit the application

Example Queries:
  • "Analyze temperature profiles in the Bay of Bengal for January 2024"
  • "Compare salinity between Arabian Sea and Bay of Bengal"
  • "Plot temperature-salinity diagram for ARGO float 1902037"
  • "Show average temperature profile in the Indian Ocean"
  • "Find profiles with temperature anomalies in the Southern Ocean"
        """
        print(help_text)
    
    def print_examples(self):
        """Print example queries."""
        examples = [
            "Analyze the average temperature profile in the Bay of Bengal for January 2024 and plot it",
            "Compare temperature and salinity profiles between Arabian Sea and Bay of Bengal",
            "Show me temperature-salinity diagrams for profiles in the Indian Ocean",
            "Find ARGO profiles with unusual temperature patterns in the Southern Ocean",
            "Plot vertical temperature profiles for float 1902037 cycles 180-190",
            "Calculate statistics for all profiles in the Bay of Bengal during 2024",
            "Show geographic distribution of ARGO floats in the Indian Ocean",
            "Analyze mixed layer depth variations in the Arabian Sea"
        ]
        
        print("\n📋 Example Queries:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")
        print()
    
    def check_system_status(self):
        """Check and display system status."""
        print("🔍 Checking system status...")
        
        try:
            status = self.workflow_engine.get_system_status()
            
            print(f"\n📊 System Status:")
            print(f"  Overall Status: {'✅ Ready' if status['system_ready'] else '❌ Issues Detected'}")
            print(f"  Recent Workflows: {status['recent_workflows']}")
            print(f"  Current Session: {status.get('current_session', 'None')}")
            
            print(f"\n🔌 Service Status:")
            for service, is_available in status['service_status'].items():
                status_icon = "✅" if is_available else "❌"
                print(f"  {service.capitalize()}: {status_icon}")
            
            if not status['system_ready']:
                print("\n⚠️  Some services are unavailable. The system may have limited functionality.")
            
        except Exception as e:
            print(f"❌ Failed to check system status: {e}")
    
    def show_history(self):
        """Show recent query history."""
        try:
            history = self.workflow_engine.get_workflow_history(limit=5)
            
            if not history:
                print("📝 No recent queries found.")
                return
            
            print("\n📝 Recent Query History:")
            for i, session in enumerate(reversed(history), 1):
                query = session.get('user_query', 'Unknown query')
                timestamp = session.get('start_time', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
                success = "✅" if session.get('success', False) else "❌"
                duration = session.get('duration', 0)
                
                print(f"  {i}. [{timestamp}] {success} ({duration:.1f}s)")
                print(f"     Query: {query[:80]}{'...' if len(query) > 80 else ''}")
            
        except Exception as e:
            print(f"❌ Failed to retrieve history: {e}")
    
    def process_query(self, user_query: str, show_technical: bool = False) -> bool:
        """
        Process a user query and display results.
        
        Args:
            user_query: The user's natural language query
            show_technical: Whether to show technical details
            
        Returns:
            True if successful, False if there was an error
        """
        try:
            print(f"\n🤔 Processing: {user_query}")
            print("⏳ Analyzing query and generating execution plan...")
            
            # Process the query
            result = self.workflow_engine.process_query(
                user_query=user_query,
                session_id=self.session_id,
                include_technical_details=show_technical
            )
            
            # Check for errors
            if "error" in result:
                print(f"\n❌ Error: {result['error']}")
                if "detailed_error" in result:
                    print(f"   Details: {result['detailed_error']}")
                return False
            
            # Display results
            self.display_results(result)
            return True
            
        except Exception as e:
            print(f"\n❌ Unexpected error: {e}")
            return False
    
    def display_results(self, result: Dict[str, Any]):
        """Display query results in a formatted way."""
        print("\n" + "="*80)
        print("📊 ANALYSIS RESULTS")
        print("="*80)
        
        # Main response
        main_response = result.get("main_response", "")
        if main_response:
            print(f"\n💡 Analysis Summary:")
            print(f"{main_response}")
        
        # Data summary
        data_summary = result.get("data_summary", {})
        if data_summary:
            print(f"\n📈 Data Summary:")
            for key, value in data_summary.items():
                print(f"  • {key.replace('_', ' ').title()}: {value}")
        
        # Visualizations
        visualizations = result.get("visualizations", [])
        if visualizations:
            print(f"\n📊 Visualizations Generated: {len(visualizations)}")
            for i, viz in enumerate(visualizations, 1):
                print(f"  {i}. {viz.get('description', 'Visualization')}")
        
        # Recommendations
        recommendations = result.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"  {i}. {rec}")
        
        # Technical details (if requested)
        technical_summary = result.get("technical_summary", "")
        if technical_summary:
            print(f"\n🔧 Technical Details:")
            print(f"{technical_summary}")
        
        # Workflow metadata
        metadata = result.get("workflow_metadata", {})
        if metadata:
            duration = metadata.get("duration_seconds", 0)
            stages = metadata.get("stages_completed", 0)
            print(f"\n⏱️  Execution Time: {duration:.2f} seconds ({stages} stages)")
    
    def run_interactive(self):
        """Run the interactive CLI."""
        self.print_banner()
        
        # Check system status on startup
        self.check_system_status()
        
        print("\n💬 Ready for your questions! Type 'help' for assistance or 'quit' to exit.")
        
        while True:
            try:
                # Get user input
                user_input = input("\n🌊 Query: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye! Thank you for using the Agentic AI ARGO Explorer!")
                    break
                
                elif user_input.lower() in ['help', '?']:
                    self.print_help()
                
                elif user_input.lower() == 'examples':
                    self.print_examples()
                
                elif user_input.lower() == 'status':
                    self.check_system_status()
                
                elif user_input.lower() == 'history':
                    self.show_history()
                
                elif user_input.lower() == 'clear':
                    os.system('clear' if os.name == 'posix' else 'cls')
                    self.print_banner()
                
                else:
                    # Process as a query
                    self.process_query(user_input)
            
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye! Thank you for using the Agentic AI ARGO Explorer!")
                break
            
            except Exception as e:
                print(f"\n❌ Unexpected error: {e}")
                print("Please try again or type 'help' for assistance.")

def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Agentic AI ARGO Data Explorer CLI")
    parser.add_argument("--query", "-q", type=str, help="Single query to process")
    parser.add_argument("--technical", "-t", action="store_true", help="Show technical details")
    parser.add_argument("--json", "-j", action="store_true", help="Output results as JSON")
    
    args = parser.parse_args()
    
    cli = CLIInterface()
    
    if args.query:
        # Single query mode
        result = cli.workflow_engine.process_query(
            user_query=args.query,
            include_technical_details=args.technical
        )
        
        if args.json:
            print(json.dumps(result, indent=2, default=str))
        else:
            if "error" in result:
                print(f"Error: {result['error']}")
                sys.exit(1)
            else:
                cli.display_results(result)
    else:
        # Interactive mode
        cli.run_interactive()

if __name__ == "__main__":
    main()
