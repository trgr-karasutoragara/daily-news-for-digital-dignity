#!/usr/bin/env python3
"""
Simple RSS to Markdown - No AI, No Complex Filtering
RSS Collection -> Direct Markdown Generation

Simplified version that focuses on reliable RSS fetching and clean markdown output.
"""

import feedparser
import requests
import time
import logging
import os
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleRSSMarkdown:
    def __init__(self, max_articles_per_source=3):
        self.output_dir = os.path.expanduser("~/Dropbox/rss-news-results/")
        self.max_articles_per_source = max_articles_per_source
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # RSS sources with global coverage
        self.rss_sources = [
            # Japan
            ("NHK NEWS WEB", "https://www3.nhk.or.jp/rss/news/cat0.xml", "Japan"),
            ("NHK Culture", "https://www3.nhk.or.jp/rss/news/cat7.xml", "Japan"),
            ("NHK International", "https://www3.nhk.or.jp/rss/news/cat6.xml", "Japan"),
            
            # China & Hong Kong
            ("China Daily", "https://www.chinadaily.com.cn/rss/world_rss.xml", "China"),
            ("South China Morning Post", "https://www.scmp.com/rss/91/feed", "Hong Kong"),
            ("CGTN", "https://www.cgtn.com/subscribe/rss.html", "China"),
            
            # Asia Pacific
            ("Channel NewsAsia", "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml", "Singapore"),
            ("Bangkok Post", "https://www.bangkokpost.com/rss/data/news.xml", "Thailand"),
            ("ABC Australia", "https://abc.net.au/news/feed/2942460/rss.xml", "Australia"),
            ("SBS Australia", "https://sbs.com.au/news/feed", "Australia"),
            
            # Europe
            ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", "Europe"),
            ("BBC Education", "http://feeds.bbci.co.uk/news/education/rss.xml", "Europe"),
            ("France24", "https://www.france24.com/en/rss", "Europe"),
            ("Deutsche Welle", "https://rss.dw.com/xml/rss-en-all", "Europe"),
            ("DR Denmark", "https://www.dr.dk/nyheder/service/feeds/senestenyt", "Europe"),
            
            # Americas
            ("NPR", "https://feeds.npr.org/1001/rss.xml", "Americas"),
            ("Buenos Aires Herald", "https://www.buenosairesherald.com/rss", "Americas"),
            
            # Middle East
            ("Haaretz", "https://www.haaretz.com/srv/haaretz-latest.rss", "Middle East"),
            ("Al Jazeera English", "https://aljazeera.com/xml/rss/all.xml", "Middle East"),
            
            # Africa
            ("Africanews", "http://www.africanews.com/feed/rss", "Africa"),
            ("AllAfrica", "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf", "Africa"),
            ("News24 South Africa", "https://feeds.24.com/articles/news24/topstories/rss", "Africa"),
            ("BBC Africa", "http://feeds.bbci.co.uk/news/world/africa/rss.xml", "Africa"),
            
            # International
            ("UN News", "https://news.un.org/feed/subscribe/en/news/all/rss.xml", "International"),
            
            # Science & Environment
            ("NASA Earth Observatory", "https://earthobservatory.nasa.gov/feeds/earth-observatory.rss", "Environment"),
            ("Science Daily", "https://www.sciencedaily.com/rss/top.xml", "Science"),
            ("Nature Climate", "http://feeds.nature.com/nclimate/rss/current", "Environment"),
            
            # Education & Culture
            ("eSchool News", "https://www.eschoolnews.com/category/top-news/feed/", "Education"),
            ("Smithsonian Insider", "https://insider.si.edu/feed/", "Culture"),
        ]

    def parse_date(self, date_string):
        """Parse various date formats from RSS feeds"""
        if not date_string:
            return None
            
        # Common RSS date formats
        date_formats = [
            '%a, %d %b %Y %H:%M:%S %z',      # RFC 2822
            '%a, %d %b %Y %H:%M:%S %Z',      # RFC 2822 with timezone name
            '%Y-%m-%dT%H:%M:%S%z',           # ISO 8601
            '%Y-%m-%dT%H:%M:%SZ',            # ISO 8601 UTC
            '%Y-%m-%d %H:%M:%S',             # Simple format
            '%Y-%m-%d',                      # Date only
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt)
            except ValueError:
                continue
        
        # If all else fails, try feedparser's built-in parsing
        try:
            import email.utils
            parsed = email.utils.parsedate_tz(date_string)
            if parsed:
                timestamp = email.utils.mktime_tz(parsed)
                return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        except:
            pass
        
        return None

    def collect_rss_feeds(self):
        """Collect RSS feeds from various sources"""
        logger.info("RSS collection started")
        
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        all_articles = []
        
        for source_name, source_url, region in self.rss_sources:
            try:
                logger.info(f"Fetching: {source_name} ({region})")
                response = requests.get(source_url, headers=headers, timeout=20)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                if feed.bozo:
                    logger.warning(f"RSS parse warning {source_name}: {feed.bozo_exception}")
                
                # Get articles from this source
                articles_from_source = 0
                for item in feed.entries:
                    if articles_from_source >= self.max_articles_per_source:
                        break
                        
                    title = getattr(item, 'title', 'No Title').strip()
                    content = (getattr(item, 'summary', '') or getattr(item, 'description', '')).strip()
                    item_url = getattr(item, 'link', '') or getattr(item, 'id', '')
                    
                    # Get publication date
                    pub_date = None
                    for date_field in ['published', 'updated', 'created']:
                        if hasattr(item, date_field):
                            pub_date = self.parse_date(getattr(item, date_field))
                            if pub_date:
                                break
                    
                    # Skip if no URL
                    if not item_url:
                        continue
                    
                    article = {
                        'title': title,
                        'content': content,
                        'url': item_url,
                        'source': source_name,
                        'region': region,
                        'published': pub_date,
                        'domain': urlparse(item_url).netloc
                    }
                    
                    all_articles.append(article)
                    articles_from_source += 1
                    logger.info(f"  Saved ({articles_from_source}): {title[:50]}...")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"RSS fetch error {source_name}: {e}")
                continue
        
        logger.info(f"RSS collection completed: {len(all_articles)} articles collected")
        return all_articles

    def generate_markdown_report(self, articles):
        """Generate markdown report from articles"""
        logger.info("Generating markdown report")
        
        if not articles:
            logger.warning("No articles to process")
            return None
        
        # Use Japan time zone (UTC+9)
        jst = timezone(timedelta(hours=9))
        report_date = datetime.now(jst).strftime('%Y-%m-%d %H:%M JST')
        
        # Group articles by region
        by_region = {}
        for article in articles:
            region = article['region']
            if region not in by_region:
                by_region[region] = []
            by_region[region].append(article)
        
        # Start markdown
        markdown = f"""# World News Collection

**Generated**: {report_date}  
**Total Articles**: {len(articles)}  
**Sources**: {len(set(article['source'] for article in articles))} RSS feeds  
**Method**: Direct RSS parsing, no AI filtering

## Coverage by Region

"""
        
        # Add region statistics
        for region, region_articles in sorted(by_region.items()):
            sources = set(article['source'] for article in region_articles)
            markdown += f"- **{region}**: {len(region_articles)} articles from {len(sources)} sources\n"
        
        markdown += "\n---\n\n"
        
        # Add articles by region
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
                
                markdown += f"""## {article['title']}

**Source**: {article['source']}  
**Published**: {pub_date_str}  
**Domain**: {article['domain']}

"""
                
                # Add content if available
                if article['content']:
                    # Clean and truncate content
                    content = article['content'].replace('\n', ' ').strip()
                    if len(content) > 400:
                        content = content[:400] + "..."
                    markdown += f"{content}\n\n"
                
                markdown += f"**[Read Full Article]({article['url']})**\n\n"
                markdown += "---\n\n"
        
        # Save to file
        jst_str = datetime.now(jst).strftime('%Y%m%d_%H%M')
        filename = f"rss_news_simple_{jst_str}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Markdown report saved: {filepath}")
        return filepath

    def run(self):
        """Main execution method"""
        logger.info("Simple RSS to Markdown started")
        
        try:
            # 1. Collect RSS feeds
            articles = self.collect_rss_feeds()
            
            if not articles:
                logger.error("No articles collected")
                return None
            
            # 2. Generate markdown report
            report_file = self.generate_markdown_report(articles)
            
            logger.info("Simple RSS to Markdown completed successfully!")
            return {
                'articles_count': len(articles),
                'report_file': report_file
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

def main():
    """Main function for execution"""
    print("=== Simple RSS to Markdown ===")
    print("No AI classification, no complex filtering")
    print("Just clean RSS collection and markdown formatting")
    print()
    
    system = SimpleRSSMarkdown()
    result = system.run()
    
    if result:
        print(f"Articles collected: {result['articles_count']}")
        print(f"Report saved: {result['report_file']}")
    else:
        print("Failed - check logs for details")

if __name__ == "__main__":
    main()
