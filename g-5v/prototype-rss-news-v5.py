#!/usr/bin/env python3
"""
Enhanced RSS News Collection - English Sources Only
Design: Global coverage through English-language sources
Benefits: Better duplicate detection, content analysis, date parsing

TECHNICAL LIMITATIONS:
- Chinese media outlets: 6 consecutive failures due to IP blocking, geographic 
  restrictions, or contractual constraints
- This is a volunteer-driven prototype (MIT License) - users can modify freely
- VPN usage avoided to prevent server burden in specific regions
- Some operational errors remain but published for transparency

Features:
- English-only sources for consistent processing
- newspaper3k integration for advanced filtering (internal use only)
- Geographic balance with major regions
- Objective filtering: newest + deduplication + regional balance
- Copyright-safe output: titles, dates, URLs only (no content redistribution)

Advanced processing (internal only):
- Enhanced duplicate detection using full article content
- Content quality assessment for filtering
- Keyword extraction for better classification
- All enhanced content used for filtering only, never redistributed
"""

import feedparser
import requests
import time
import logging
import os
import hashlib
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Optional: Advanced content processing
try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    print("Optional: pip install newspaper3k for enhanced content analysis")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RSSNewsPrototype:
    def __init__(self, news_max_hours=48, slow_max_days=7, max_workers=12, target_timeout=8):
        self.output_dir = os.path.expanduser("~/Dropbox/rss-news-results/")
        self.news_max_hours = news_max_hours
        self.slow_max_days = slow_max_days
        self.max_workers = max_workers
        self.target_timeout = target_timeout
        
        os.makedirs(self.output_dir, exist_ok=True)
        
        # All English sources for consistent processing
        self.rss_sources = [
            # Asia Pacific (English editions)
            ("NHK World Japan", "https://www3.nhk.or.jp/rss/news/cat6.xml", "Japan", "news"),
            ("Channel NewsAsia", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "Singapore", "news"),
            ("ABC News Australia", "https://abc.net.au/news/feed/2942460/rss.xml", "Australia", "news"),
            ("SBS News Australia", "https://sbs.com.au/news/feed", "Australia", "news"),
            ("South China Morning Post", "https://www.scmp.com/rss/91/feed", "Hong Kong", "news"),
            ("Times of India", "https://timesofindia.indiatimes.com/rssfeeds/296589292.cms", "South Asia", "news"),
            ("Bangkok Post", "https://www.bangkokpost.com/rss/data/news.xml", "Southeast Asia", "news"),
            ("Straits Times Singapore", "https://www.straitstimes.com/news/world/rss.xml", "Singapore", "news"),
            
            # Europe (English editions)
            ("BBC World News", "http://feeds.bbci.co.uk/news/world/rss.xml", "Europe", "news"),
            ("France24 English", "https://www.france24.com/en/rss", "Europe", "news"),
            ("Deutsche Welle English", "https://rss.dw.com/xml/rss-en-all", "Europe", "news"),
            ("Euronews English", "https://feeds.feedburner.com/euronews/en/news", "Europe", "news"),
            
            # Americas
            ("NPR World News", "https://feeds.npr.org/1001/rss.xml", "North America", "news"),
            ("CBC World News", "https://rss.cbc.ca/lineup/world.xml", "North America", "news"),
            ("Buenos Aires Herald", "https://buenosairesherald.com/rss", "Latin America", "news"),
            
            # Africa (English sources)
            ("BBC Africa", "http://feeds.bbci.co.uk/news/world/africa/rss.xml", "Africa", "news"),
            ("AllAfrica", "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "Africa", "news"),
            ("Mail & Guardian", "https://mg.co.za/rss/", "Africa", "news"),
            ("Africanews", "https://www.africanews.com/feed/rss", "Africa", "news"),
            
            # Middle East (English sources)
            ("Al Jazeera English", "https://www.aljazeera.com/xml/rss/all.xml", "Middle East", "news"),
            ("Jerusalem Post", "https://www.jpost.com/rss/rssfeedsheadlines.aspx", "Middle East", "news"),
            ("Arab News", "https://www.arabnews.com/rss.xml", "Middle East", "news"),
            
            # International Organizations (slower update)
            ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "International", "slow"),
            
            # Environment & Science (slower update)
            ("Carbon Brief", "https://www.carbonbrief.org/rss", "Environment", "slow"),
            ("Climate Home News", "https://www.climatechangenews.com/feed/", "Environment", "slow"),
            ("Science Daily", "https://www.sciencedaily.com/rss/all.xml", "Science", "slow"),
            ("NASA Earth Observatory", "https://earthobservatory.nasa.gov/feeds/earth-observatory.rss", "Environment", "slow"),
            ("Nature Climate", "http://feeds.nature.com/nclimate/rss/current", "Environment", "slow"),
        ]
        
        # Performance tracking
        self.source_performance = {}
        self.articles_lock = Lock()

    def enhance_article_content(self, article):
        """Enhanced content processing for filtering only (no redistribution)"""
        if not NEWSPAPER_AVAILABLE:
            return article
        
        try:
            news_article = Article(article['url'])
            news_article.download()
            news_article.parse()
            
            # Store enhanced content for internal filtering only
            if news_article.text and len(news_article.text) > len(article.get('content', '')):
                article['_internal_content'] = news_article.text  # Internal use only
                article['content_quality'] = 'enhanced'
            
            # Store keywords for internal duplicate detection only
            if hasattr(news_article, 'keywords') and news_article.keywords:
                article['_internal_keywords'] = news_article.keywords[:5]  # Internal use only
                
        except Exception as e:
            logger.debug(f"Content enhancement failed for {article['url']}: {e}")
            article['content_quality'] = 'basic'
        
        return article

    def intelligent_duplicate_detection(self, articles):
        """Enhanced duplicate detection using internal content (no redistribution)"""
        unique_articles = []
        seen_signatures = set()
        
        for article in articles:
            # Create content signature from title and internal content
            title_words = article['title'].lower().split()
            # Use internal content for duplicate detection only (never redistributed)
            internal_content = article.get('_internal_content', article.get('_internal_rss_content', ''))
            content_words = internal_content.lower().split()[:20]  # First 20 words
            
            # Remove common English stop words
            stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'a', 'an'}
            
            significant_words = [w for w in title_words + content_words 
                               if len(w) > 3 and w not in stop_words]
            
            # Create content signature (first 6 significant words)
            if len(significant_words) >= 4:
                content_signature = ' '.join(sorted(significant_words[:6]))
                signature_hash = hashlib.md5(content_signature.encode()).hexdigest()[:12]
                
                if signature_hash not in seen_signatures:
                    seen_signatures.add(signature_hash)
                    # Clean internal data before adding to results
                    clean_article = article.copy()
                    clean_article.pop('_internal_content', None)
                    clean_article.pop('_internal_keywords', None)
                    clean_article.pop('_internal_rss_content', None)
                    unique_articles.append(clean_article)
                else:
                    logger.debug(f"Enhanced duplicate removed: {article['title'][:50]}...")
            else:
                # Keep articles with insufficient content for signature
                clean_article = article.copy()
                clean_article.pop('_internal_content', None)
                clean_article.pop('_internal_keywords', None)
                clean_article.pop('_internal_rss_content', None)
                unique_articles.append(clean_article)
        
        logger.info(f"Enhanced deduplication: {len(articles)} → {len(unique_articles)} articles")
        return unique_articles

    def balanced_regional_coverage(self, articles, max_per_region=None):
        """Smart regional balance based on actual content availability"""
        by_region = {}
        for article in articles:
            region = article['region']
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(article)
        
        # Dynamic limits based on region size and importance
        region_limits = {
            'International': 25,
            'Europe': 30,
            'North America': 25,
            'Africa': 25,  # Increased due to 4 sources
            'Middle East': 20,
            'Latin America': 15,
            'Environment': 15,
            'Science': 15,
            'China': 20,
            'Hong Kong': 20,
            'Japan': 20,
            'Singapore': 20,
            'Australia': 20,
            'South Asia': 20,
            'Southeast Asia': 20,
        }
        
        # Sort articles within each region by publication date (newest first)
        for region in by_region:
            by_region[region].sort(
                key=lambda x: x['published'] or datetime.min.replace(tzinfo=timezone.utc), 
                reverse=True
            )
        
        balanced_articles = []
        for region, region_articles in by_region.items():
            # Use specific limit or default
            limit = region_limits.get(region, max_per_region or 20)
            selected = region_articles[:limit]
            balanced_articles.extend(selected)
            
            logger.info(f"Regional balance: {region} - {len(selected)}/{len(region_articles)} articles (limit: {limit})")
        
        return balanced_articles

    def fetch_single_rss_robust(self, source):
        """Enhanced RSS fetching with better error handling"""
        source_name, url, region = source[:3]
        source_type = source[3] if len(source) > 3 else "news"
        
        start_time = time.time()
        
        try:
            # Enhanced headers for better compatibility
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; NewsAggregator/1.0; +https://example.com/bot)',
                'Accept': 'application/rss+xml, application/xml, text/xml, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate',
                'Cache-Control': 'no-cache'
            }
            
            timeout = self.target_timeout if source_type == "news" else self.target_timeout + 3
            
            response = requests.get(url, timeout=timeout, headers=headers, verify=True)
            response.raise_for_status()
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                logger.warning(f"No entries found in {source_name}")
                return []
            
            articles = []
            current_time = datetime.now(timezone.utc)
            
            # Set time limit based on source type
            if source_type == "news":
                time_limit = current_time - timedelta(hours=self.news_max_hours)
            else:
                time_limit = current_time - timedelta(days=self.slow_max_days)
            
            for entry in feed.entries[:50]:  # Process more entries for better selection
                try:
                    # Enhanced date parsing
                    pub_date = None
                    
                    # Try multiple date fields
                    for date_field in ['published_parsed', 'updated_parsed', 'created_parsed']:
                        if hasattr(entry, date_field) and getattr(entry, date_field):
                            try:
                                date_tuple = getattr(entry, date_field)
                                pub_date = datetime(*date_tuple[:6], tzinfo=timezone.utc)
                                break
                            except (TypeError, ValueError):
                                continue
                    
                    # Skip if too old
                    if pub_date and pub_date < time_limit:
                        continue
                    
                    # Extract minimal content for internal processing only
                    title = entry.get('title', 'No title').strip()
                    internal_content = ''
                    
                    # Try multiple content fields for internal duplicate detection only
                    for content_field in ['summary', 'description', 'content']:
                        if hasattr(entry, content_field):
                            field_content = getattr(entry, content_field)
                            if isinstance(field_content, list) and field_content:
                                internal_content = field_content[0].get('value', '')
                            elif isinstance(field_content, str):
                                internal_content = field_content
                            if internal_content:
                                break
                    
                    # Get URL with fallbacks
                    item_url = entry.get('link', entry.get('id', ''))
                    if not item_url or not item_url.startswith('http'):
                        continue
                    
                    article = {
                        'title': title,
                        'content': '',  # No content in output for copyright safety
                        '_internal_rss_content': internal_content,  # Internal use only
                        'url': item_url,
                        'source': source_name,
                        'region': region,
                        'published': pub_date,
                        'domain': urlparse(item_url).netloc,
                        'source_type': source_type,
                        'content_quality': 'basic'
                    }
                    
                    # Enhanced content processing if available
                    if NEWSPAPER_AVAILABLE:
                        article = self.enhance_article_content(article)
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.debug(f"Entry parsing error in {source_name}: {e}")
                    continue
            
            fetch_time = time.time() - start_time
            logger.info(f"✓ {source_name}: {len(articles)} articles in {fetch_time:.2f}s")
            return articles
            
        except requests.exceptions.RequestException as e:
            fetch_time = time.time() - start_time
            logger.error(f"✗ Request error {source_name} in {fetch_time:.2f}s: {e}")
            return []
        except Exception as e:
            fetch_time = time.time() - start_time
            logger.error(f"✗ General error {source_name} in {fetch_time:.2f}s: {e}")
            return []

    def collect_all_rss_feeds(self):
        """Enhanced parallel RSS collection"""
        logger.info("Starting RSS collection (workers: {self.max_workers})")
        logger.info(f"Sources: {len(self.rss_sources)} English-language outlets")
        start_time = time.time()
        
        all_articles = []
        successful_sources = 0
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all source fetch tasks
            future_to_source = {
                executor.submit(self.fetch_single_rss_robust, source): source[0] 
                for source in self.rss_sources
            }
            
            # Collect results as they complete
            completed = 0
            for future in as_completed(future_to_source):
                source_name = future_to_source[future]
                completed += 1
                
                try:
                    articles = future.result()
                    all_articles.extend(articles)
                    if articles:
                        successful_sources += 1
                    
                    # Progress reporting
                    progress = (completed / len(self.rss_sources)) * 100
                    logger.info(f"Progress: {progress:.0f}% ({completed}/{len(self.rss_sources)}) - Raw articles: {len(all_articles)}")
                    
                except Exception as e:
                    logger.error(f"Processing error for {source_name}: {e}")
        
        raw_count = len(all_articles)
        
        # Apply enhanced quality filters
        logger.info("Applying enhanced quality filters...")
        
        # 1. Enhanced duplicate detection
        all_articles = self.intelligent_duplicate_detection(all_articles)
        
        # 2. Smart regional balance
        all_articles = self.balanced_regional_coverage(all_articles)
        
        # 3. Final sort by publication date (newest first)
        all_articles.sort(
            key=lambda x: x['published'] or datetime.min.replace(tzinfo=timezone.utc), 
            reverse=True
        )
        
        end_time = time.time()
        logger.info(f"Collection completed: {raw_count} → {len(all_articles)} articles from {successful_sources}/{len(self.rss_sources)} sources in {end_time - start_time:.2f} seconds")
        
        return all_articles, successful_sources

    def generate_enhanced_markdown_report(self, articles, successful_sources):
        """Generate markdown report with minimal content (copyright-safe)"""
        logger.info(f"Generating copyright-safe markdown report for {len(articles)} articles")
        
        if not articles:
            logger.warning("No articles to process")
            return None
        
        jst = timezone(timedelta(hours=9))
        report_date = datetime.now(jst).strftime('%Y-%m-%d %H:%M JST')
        
        # Group articles by region
        by_region = {}
        enhanced_count = 0
        for article in articles:
            region = article['region']
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(article)
            
            if article.get('content_quality') == 'enhanced':
                enhanced_count += 1
        
        markdown = f"""# RSS News Prototype

**Generated**: {report_date}  
**Total Articles**: {len(articles)}  
**Sources**: {successful_sources}/{len(self.rss_sources)} English RSS feeds successful  
**Enhancement**: {enhanced_count} articles processed with advanced filtering  
**Method**: English-only sources + Enhanced duplicate detection + Smart regional balance  
**Output**: Copyright-safe titles, dates, and URLs only

## Coverage by Region

"""
        
        # Add region statistics
        for region, region_articles in sorted(by_region.items()):
            sources = set(article['source'] for article in region_articles)
            enhanced = sum(1 for a in region_articles if a.get('content_quality') == 'enhanced')
            markdown += f"- **{region}**: {len(region_articles)} articles from {len(sources)} sources"
            if enhanced > 0:
                markdown += f" ({enhanced} enhanced filtering)"
            markdown += "\n"
        
        markdown += "\n---\n\n"
        
        # Add articles by region with minimal information only
        for region in sorted(by_region.keys()):
            region_articles = by_region[region]
            if not region_articles:
                continue
            
            markdown += f"# {region} ({len(region_articles)} articles)\n\n"
            
            for article in region_articles:
                # Format publication date
                pub_date_str = "Date unknown"
                if article['published']:
                    try:
                        pub_date_str = article['published'].strftime('%Y-%m-%d %H:%M UTC')
                    except:
                        pub_date_str = str(article['published'])
                
                # Quality indicator for transparency
                quality_indicator = ""
                if article.get('content_quality') == 'enhanced':
                    quality_indicator = " ✓"
                
                # Minimal output: title, source, date, URL only
                markdown += f"""## {article['title']}{quality_indicator}

**Source**: {article['source']} ({article['region']})  
**Published**: {pub_date_str}  
**Domain**: {article['domain']}

**[Read Full Article]({article['url']})**

---

"""
        
        # Save to file with original naming convention
        jst_str = datetime.now(jst).strftime('%Y%m%d_%H%M')
        filename = f"rss_news_{jst_str}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Copyright-safe markdown report saved: {filepath}")
        return filepath

    def run(self):
        """Main execution method"""
        logger.info("RSS News Prototype started")
        
        try:
            # 1. Collect RSS feeds
            articles, successful_sources = self.collect_all_rss_feeds()
            
            if not articles:
                logger.error("No articles collected")
                return None
            
            # 2. Generate enhanced markdown report
            report_file = self.generate_enhanced_markdown_report(articles, successful_sources)
            
            logger.info("RSS News Prototype completed successfully!")
            return {
                'articles_count': len(articles),
                'successful_sources': successful_sources,
                'total_sources': len(self.rss_sources),
                'success_rate': f"{(successful_sources/len(self.rss_sources)*100):.1f}%",
                'report_file': report_file,
                'enhancement_available': NEWSPAPER_AVAILABLE
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

def main():
    """Main function"""
    print("=== RSS News Prototype ===")
    print("Design: Global coverage through English-language sources")
    print("Processing: Advanced filtering and duplicate detection")
    print("Output: Copyright-safe (titles, dates, URLs only)")
    print()
    
    if NEWSPAPER_AVAILABLE:
        print("✓ newspaper3k available - Enhanced filtering enabled")
        print("  • Advanced duplicate detection")
        print("  • Content quality assessment")
        print("  • Internal processing only (no content redistribution)")
    else:
        print("ℹ  Install newspaper3k for enhanced filtering: pip install newspaper3k")
        print("  • Basic duplicate detection enabled")
    print()
    
    # Configuration
    collector = RSSNewsPrototype(
        news_max_hours=48,    # News sources: 48 hours
        slow_max_days=7,      # Specialized sources: 7 days
        max_workers=12,       # Parallel processing
        target_timeout=8      # Timeout per source
    )
    
    result = collector.run()
    
    if result:
        print(f"✓ Success!")
        print(f"Articles collected: {result['articles_count']}")
        print(f"Successful sources: {result['successful_sources']}/{result['total_sources']} ({result['success_rate']})")
        print(f"Enhanced filtering: {'Enabled' if result['enhancement_available'] else 'Basic mode'}")
        print(f"Output format: Copyright-safe minimal information")
        print(f"Report saved: {result['report_file']}")
    else:
        print("✗ Failed - check logs for details")

if __name__ == "__main__":
    main()
