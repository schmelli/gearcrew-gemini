#!/usr/bin/env python3
"""
GearCrew CLI Runner - Run the multi-agent system with live output.

Usage:
  python run_crew.py                          # Interactive mode
  python run_crew.py --playlist "GearGraph Material"
  python run_crew.py --url "https://youtube.com/watch?v=..."
  python run_crew.py --manufacturer "Durston Gear"
"""
import os
import sys
import argparse
import logging
from datetime import datetime
from typing import Optional, List

# Enable interactive mode
os.environ["GEARCREW_INTERACTIVE"] = "true"

# Setup colored logging
class ColoredFormatter(logging.Formatter):
    """Colored log formatter"""
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.RESET)
        record.levelname = f"{color}{record.levelname}{self.RESET}"
        record.msg = f"{record.msg}"
        return super().format(record)


def setup_logging(verbose: bool = False):
    """Setup logging with colors"""
    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler()
    handler.setFormatter(ColoredFormatter(
        '%(asctime)s │ %(levelname)-18s │ %(message)s',
        datefmt='%H:%M:%S'
    ))
    logging.basicConfig(level=level, handlers=[handler])


def print_banner():
    """Print startup banner"""
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║   ⚙️  GearCrew Multi-Agent System                                 ║
║                                                                   ║
║   Hierarchical AI agents for outdoor gear research                ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
    """)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}\n")


def run_playlist_scan(playlist: str, max_videos: int = 20):
    """Scan videos from a YouTube playlist"""
    print_section(f"📺 Scanning YouTube Playlist: {playlist}")

    from src.tools.youtube_playlist_tool import YouTubePlaylistTool

    tool = YouTubePlaylistTool()
    result = tool._run(playlist, max_videos)
    print(result)

    return result


def run_full_flow(
    sources: Optional[List[str]] = None,
    source_type: str = "auto",
    max_items: int = 20,
    require_approval: bool = True
):
    """Run the complete GearCollection flow"""
    print_section("🚀 Starting GearCrew Flow")

    from src.flows.gear_collection_flow import GearCollectionFlow
    from src.utils.monitoring import get_monitor

    monitor = get_monitor()

    try:
        # Start flow
        monitor.start_flow("GearCollectionFlow")
        print("✓ Flow initialized")

        flow = GearCollectionFlow()

        # Configure state
        flow.state.quality_threshold = 0.85
        flow.state.max_parallel_scans = 4

        print("✓ State configured")
        print(f"  • Quality threshold: {flow.state.quality_threshold}")
        print(f"  • Max parallel scans: {flow.state.max_parallel_scans}")

        # Prepare inputs
        inputs = {
            "sources": sources or [],
            "source_type": source_type,
            "max_items": max_items,
            "require_approval": require_approval
        }

        print_section("🔎 Phase 1: Discovery (Gear-heads)")
        print("Starting scanner agents...")

        # Note: In a real run, this would execute the full flow
        # For demo purposes, we show the structure
        print("\n⚡ Agents would execute here:")
        print("  • YouTube Scanner - scanning videos...")
        print("  • Website Scanner - checking manufacturer sites...")
        print("  • Blog Scanner - reading gear blogs...")
        print("  • Reddit Scanner - monitoring discussions...")

        print_section("📚 Phase 2: Curation (Curators)")
        print("Research agents verifying discoveries...")
        print("\n⚡ Agents would execute here:")
        print("  • Graph Verifier - checking existing data...")
        print("  • Autonomous Researcher - gathering specs...")
        print("  • Data Validator - quality checks...")
        print("  • Citation Agent - documenting sources...")

        print_section("🏗️ Phase 3: Graph Loading (Architects)")
        print("Preparing safe graph updates...")
        print("\n⚡ Agents would execute here:")
        print("  • Cypher Validator - reviewing code...")
        print("  • Relationship Gardener - checking integrity...")

        # Complete
        monitor.end_flow(discoveries=0, nodes=0, quality=0.0)

        print_section("✅ Flow Complete")
        print(monitor.get_summary())

        return {"status": "demo_complete"}

    except KeyboardInterrupt:
        print("\n\n⏹️ Flow interrupted by user")
        return {"status": "interrupted"}

    except Exception as e:
        logging.error(f"Flow error: {e}")
        monitor.log_error("flow", str(e))
        raise


def interactive_mode():
    """Run in interactive mode with prompts"""
    print_section("🎮 Interactive Mode")

    print("What would you like to scan?\n")
    print("  1. YouTube Playlist")
    print("  2. Specific YouTube Video")
    print("  3. Manufacturer Website")
    print("  4. Search YouTube")
    print("  5. Run Full Discovery Flow")
    print("  6. Exit")

    choice = input("\nEnter choice (1-6): ").strip()

    if choice == "1":
        playlist = input("Enter playlist name or URL: ").strip()
        if playlist:
            run_playlist_scan(playlist)

    elif choice == "2":
        url = input("Enter video URL: ").strip()
        if url:
            print(f"\nWould scan video: {url}")
            print("(YouTube transcript extraction would happen here)")

    elif choice == "3":
        print("\nAvailable manufacturers:")
        manufacturers = ["Durston Gear", "Zpacks", "Hyperlite Mountain Gear",
                        "NEMO Equipment", "Big Agnes", "Custom URL"]
        for i, m in enumerate(manufacturers, 1):
            print(f"  {i}. {m}")
        m_choice = input("Select (1-6): ").strip()
        print(f"\nWould scan manufacturer website...")

    elif choice == "4":
        query = input("Enter search query: ").strip()
        if query:
            print(f"\nWould search YouTube for: {query}")

    elif choice == "5":
        require_approval = input("Require approval before graph load? (y/n): ").lower() == 'y'
        run_full_flow(require_approval=require_approval)

    elif choice == "6":
        print("\nGoodbye! 👋")
        return

    else:
        print("\nInvalid choice")

    # Continue interactive mode
    input("\nPress Enter to continue...")
    interactive_mode()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="GearCrew Multi-Agent System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--playlist', '-p',
        help="YouTube playlist URL or name to scan"
    )
    parser.add_argument(
        '--url', '-u',
        action='append',
        help="Specific URL(s) to scan (can be used multiple times)"
    )
    parser.add_argument(
        '--manufacturer', '-m',
        help="Manufacturer website to scan"
    )
    parser.add_argument(
        '--search', '-s',
        help="YouTube search query"
    )
    parser.add_argument(
        '--max-items', '-n',
        type=int,
        default=20,
        help="Maximum items to process (default: 20)"
    )
    parser.add_argument(
        '--no-approval',
        action='store_true',
        help="Skip human approval for graph loading"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose logging"
    )
    parser.add_argument(
        '--monitor', '-M',
        action='store_true',
        help="Launch Streamlit monitoring UI"
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(args.verbose)
    print_banner()

    # Launch monitor UI
    if args.monitor:
        print("Launching Streamlit monitor...")
        os.system("streamlit run crew_monitor.py")
        return

    # Handle specific commands
    if args.playlist:
        run_playlist_scan(args.playlist, args.max_items)

    elif args.url:
        print_section(f"📺 Scanning {len(args.url)} URL(s)")
        for url in args.url:
            print(f"  • {url}")
        run_full_flow(
            sources=args.url,
            source_type="url",
            max_items=args.max_items,
            require_approval=not args.no_approval
        )

    elif args.manufacturer:
        print_section(f"🏭 Scanning Manufacturer: {args.manufacturer}")
        run_full_flow(
            sources=[args.manufacturer],
            source_type="manufacturer",
            max_items=args.max_items,
            require_approval=not args.no_approval
        )

    elif args.search:
        print_section(f"🔍 YouTube Search: {args.search}")
        print("(Search functionality would execute here)")

    else:
        # No arguments - interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
