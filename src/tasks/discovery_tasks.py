"""
Discovery Tasks - Task definitions for the Gear-heads scanning team
"""
from crewai import Task
from typing import List


def create_discovery_tasks(manager, youtube_scanner, website_scanner,
                           blog_scanner, reddit_scanner) -> List[Task]:
    """
    Create all discovery tasks for the Gear-heads crew.

    Args:
        manager: Discovery Manager agent
        youtube_scanner: YouTube Scanner agent
        website_scanner: Website Scanner agent
        blog_scanner: Blog Scanner agent
        reddit_scanner: Reddit Scanner agent

    Returns:
        List of Task objects in execution order
    """

    # Parallel scanning tasks (async_execution=True)
    youtube_scan_task = Task(
        description="""Scan YouTube for new gear review videos.

        **Your Mission**:
        1. Search for recent gear review uploads (past week)
        2. Check Source Registry - skip already-scanned videos
        3. Extract product mentions from video transcripts and descriptions
        4. Create ProductDiscovery objects for each gear item found
        5. Create InsightDiscovery objects for useful tips/tricks mentioned
        6. Enqueue all discoveries with appropriate priority
        7. Register video URLs in Source Registry

        **Target Search Terms**:
        - "ultralight backpacking gear review"
        - "tent review 2025"
        - "backpack review"
        - "sleeping bag review"
        - "hiking gear"
        - Plus specific brand names (Durston, Zpacks, HMG, etc.)

        **Priority Guidelines**:
        - Dedicated product review: Priority 8-10
        - Gear comparison video: Priority 7-9
        - Gear list/recommendations: Priority 6-8
        - Casual mention in trip video: Priority 4-6

        **Output Format**: Return a list of discovery IDs that were enqueued.
        """,
        expected_output="List of discovery IDs enqueued with source citations and priority scores",
        agent=youtube_scanner,
        async_execution=True  # Runs in parallel with other scanners
    )

    website_scan_task = Task(
        description="""Scan manufacturer websites for new products and updates.

        **Your Mission**:
        1. Visit priority manufacturer websites
        2. Check Source Registry to avoid duplicate scans
        3. Navigate to product pages (/products, /shop, /gear)
        4. Extract product specifications using Firecrawl
        5. Create ProductDiscovery objects with verified manufacturer data
        6. Enqueue with high priority (9-10) - authoritative source
        7. Register pages in Source Registry

        **Priority Manufacturers** (scan in this order):
        - Durston Gear (new product announcements)
        - Zpacks (frequent updates)
        - Hyperlite Mountain Gear
        - NEMO Equipment
        - Big Agnes
        - Enlightened Equipment
        - Western Mountaineering
        - ULA Equipment
        - Gossamer Gear

        **Focus On**:
        - "New" or "Just Released" products
        - Products not yet in our database
        - Updated specifications for existing products
        - Limited edition or seasonal items

        **Data Quality**:
        - Confidence score: 0.95-1.0 (manufacturer source)
        - Priority: 9-10
        - Extract ALL official specs
        - Include product images and URLs

        **Output Format**: Return list of product discoveries with complete specifications.
        """,
        expected_output="List of ProductDiscovery objects with verified manufacturer data and high confidence scores",
        agent=website_scanner,
        async_execution=True
    )

    blog_scan_task = Task(
        description="""Scan outdoor gear blogs for reviews and field reports.

        **Your Mission**:
        1. Monitor priority blog sources for new posts
        2. Check Source Registry - skip already-scanned articles
        3. Read articles using Firecrawl
        4. Extract product mentions and reviewer assessments
        5. Capture insights and practical tips
        6. Create appropriate discoveries (products, insights)
        7. Enqueue with priority based on content quality
        8. Register article URLs in Source Registry

        **Priority Blogs to Monitor**:
        - OutdoorGearLab (detailed testing data)
        - Halfway Anywhere (thru-hiker annual surveys)
        - The Trek (long-distance hiker reports)
        - SectionHiker (comprehensive reviews)
        - Andrew Skurka (expert insights)

        **Content Types**:
        - Product reviews: Extract verdict, pros/cons, specs
        - Comparison articles: Note products and rankings
        - Field reports: Capture real-world usage notes
        - Gear lists: Extract equipment configurations
        - How-to articles: Create InsightDiscovery objects

        **Priority Assignment**:
        - In-depth review: Priority 8-10
        - Comparison article: Priority 7-9
        - Field report: Priority 6-8
        - Gear list: Priority 5-7

        **Quality Standards**:
        - Include direct quotes for key points
        - Note reviewer credentials
        - Flag sponsored vs independent content
        - Extract any test measurements

        **Output Format**: Return discoveries with context from article.
        """,
        expected_output="List of discoveries (products and insights) with article context and reviewer assessments",
        agent=blog_scanner,
        async_execution=True
    )

    reddit_scan_task = Task(
        description="""Monitor Reddit and outdoor forums for gear discussions.

        **Your Mission**:
        1. Monitor r/Ultralight and other priority subreddits
        2. Check Source Registry - skip processed threads
        3. Filter for high-value discussions (50+ upvotes/comments)
        4. Extract product mentions and community sentiment
        5. Capture crowd-sourced insights and consensus
        6. Create discoveries with community context
        7. Enqueue based on engagement and information quality
        8. Register thread URLs in Source Registry

        **Priority Communities**:
        - r/Ultralight (highest priority)
        - r/Ul_Gear
        - r/CampingGear
        - r/WildernessBackpacking
        - WhiteBlaze forums
        - Backpacking Light forums

        **High-Value Thread Types**:
        - Shakedown posts (gear list reviews)
        - "Best gear of 202X" discussions
        - Detailed product comparisons
        - Trip reports with gear lists
        - "Alternatives to X" threads

        **Engagement Thresholds**:
        - 100+ upvotes: Priority 8-10
        - 50-99 upvotes: Priority 6-8
        - 25-49 upvotes: Priority 4-6
        - 50+ comments: +1 priority boost

        **Community Insights to Extract**:
        - Consensus recommendations
        - Common product issues
        - Popular modifications
        - Budget alternatives
        - Things to avoid

        **Output Format**: Return discoveries with community context and engagement metrics.
        """,
        expected_output="List of discoveries with community sentiment, engagement metrics, and crowd-sourced insights",
        agent=reddit_scanner,
        async_execution=True
    )

    # Aggregation task (waits for all scanners)
    aggregate_task = Task(
        description="""Aggregate and prioritize discoveries from all scanners.

        **Your Mission**:
        1. Wait for all scanner agents to complete their tasks
        2. Collect all discoveries from the Discovery Queue
        3. Identify and handle duplicates:
           - Same product found across multiple sources
           - Merge information from multiple sources
           - Prioritize manufacturer data over third-party
        4. Calculate final priority scores:
           - Consider source authority
           - Factor in information completeness
           - Boost products mentioned across multiple sources
        5. Generate summary statistics:
           - Total discoveries by type (product, insight, brand)
           - Discoveries by source (YouTube, websites, blogs, Reddit)
           - Priority distribution
           - Quality metrics
        6. Prepare handoff to Curators team:
           - Queue status check
           - Top priority items summary
           - Recommendations for immediate research

        **Deduplication Logic**:
        - Match products by name + brand
        - Merge specs from multiple sources
        - Keep highest quality source URL
        - Average confidence scores
        - Sum priority scores (cap at 10)

        **Summary Report Should Include**:
        - Total discoveries: X products, Y insights, Z brands
        - Source breakdown: YouTube (N), Websites (N), Blogs (N), Reddit (N)
        - Priority distribution: High (8-10): N, Medium (5-7): N, Low (1-4): N
        - Top 10 priority items ready for curation
        - Recommendations for Curators team

        **Output Format**: Structured summary report with statistics and recommendations.
        """,
        expected_output="""Aggregated discovery report including:
        - Total counts by type and source
        - Deduplicated product list
        - Priority rankings
        - Top items ready for Curators
        - Quality metrics and recommendations""",
        agent=manager,
        context=[youtube_scan_task, website_scan_task, blog_scan_task, reddit_scan_task]
    )

    return [
        youtube_scan_task,
        website_scan_task,
        blog_scan_task,
        reddit_scan_task,
        aggregate_task
    ]
