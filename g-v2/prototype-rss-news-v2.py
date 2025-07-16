#!/usr/bin/env python3
"""
prototype-rss-news - Classification with Reasoning (Qwen2.5VL:7B)
RSS Collection -> Qwen2.5VL 7B Classification with Reasoning -> English Markdown Generation

Modified for qwen2.5vl:7b model with classification reasoning and English output
"""

import sqlite3
import feedparser
import requests
import time
import logging
import re
import os
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrototypeRSSNews:
    def __init__(self, db_path="prototype_rss_news.db"):
        self.db_path = db_path
        self.ollama_url = "http://localhost:11434"
        self.model = "qwen2.5vl:7b"
        self.output_dir = os.path.expanduser("~/Dropbox/rss-news-results/")
        self.init_database()
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Enhanced RSS sources with global coverage
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

    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if table exists and has correct schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='news_items';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            # Check if reasoning column exists
            cursor.execute("PRAGMA table_info(news_items);")
            columns = [row[1] for row in cursor.fetchall()]
            if 'reasoning' not in columns:
                logger.info("Updating database schema - adding reasoning column")
                cursor.execute("DROP TABLE news_items")
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title_original TEXT,
            title_jp TEXT,
            content_original TEXT,
            content_jp TEXT,
            source_name TEXT,
            url TEXT,
            language TEXT,
            importance INTEGER DEFAULT 2,
            scope INTEGER DEFAULT 2,
            category TEXT DEFAULT 'Other',
            reasoning TEXT,
            processed BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def check_environment(self):
        """Check Ollama and Qwen2.5VL availability"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any('qwen2.5vl:7b' in model.get('name', '') for model in models):
                    return True
        except:
            pass
        
        logger.error("Ollama with qwen2.5vl:7b is not available. Please install and start Ollama with qwen2.5vl:7b model.")
        return False

    def collect_rss_feeds(self):
        logger.info("RSS collection started")
        
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'}
        saved_count = 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for source_name, source_url, region in self.rss_sources:
            try:
                logger.info(f"Fetching: {source_name} ({region})")
                response = requests.get(source_url, headers=headers, timeout=20)
                response.raise_for_status()
                
                feed = feedparser.parse(response.content)
                
                if feed.bozo:
                    logger.warning(f"RSS parse warning {source_name}: {feed.bozo_exception}")
                
                # Get 2 items per source
                for item in feed.entries[:2]:
                    title = getattr(item, 'title', 'No Title')
                    content = getattr(item, 'summary', '') or getattr(item, 'description', '')
                    item_url = getattr(item, 'link', '') or getattr(item, 'id', '')
                    
                    if not item_url:
                        continue
                    
                    # Duplicate check
                    cursor.execute('SELECT COUNT(*) FROM news_items WHERE url = ?', (item_url,))
                    if cursor.fetchone()[0] > 0:
                        continue
                    
                    cursor.execute('''
                    INSERT INTO news_items (title_original, content_original, source_name, url, language)
                    VALUES (?, ?, ?, ?, ?)
                    ''', (title, content[:1000], source_name, item_url, 'unknown'))
                    
                    saved_count += 1
                    logger.info(f"  Saved ({saved_count}): {title[:50]}...")
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"RSS fetch error {source_name}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"RSS collection completed: {saved_count} items")
        return saved_count

    def call_ollama(self, prompt):
        try:
            data = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }
            
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=data,
                timeout=90
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get('response', '').strip()
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            return None

    def process_articles(self):
        logger.info(f"Article classification started with {self.model}")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, title_original, content_original
        FROM news_items 
        WHERE processed = FALSE
        ''')
        
        items = cursor.fetchall()
        
        if not items:
            logger.info("No items to process")
            return 0
        
        processed_count = 0
        
        for item_id, title, content in items:
            logger.info(f"Classifying ({processed_count+1}/{len(items)}): {title[:40]}...")
            
            try:
                # Keep original text as is
                title_jp = title
                content_jp = content
                
                importance, scope, category, reasoning = self.classify_article(title, content)
                
                cursor.execute('''
                UPDATE news_items 
                SET title_jp = ?, content_jp = ?, importance = ?, scope = ?, category = ?, reasoning = ?, processed = TRUE
                WHERE id = ?
                ''', (title_jp, content_jp, importance, scope, category, reasoning, item_id))
                
                processed_count += 1
                logger.info(f"  Classified: {category} (Importance:{importance}, Scope:{scope})")
                time.sleep(2)  # API rate limiting
                
            except Exception as e:
                logger.error(f"Classification error ID {item_id}: {e}")
                # Skip this item and continue
                continue
        
        conn.commit()
        conn.close()
        
        logger.info(f"Classification completed: {processed_count} items")
        return processed_count

    def classify_article(self, title, content):
        prompt = f"""
Classify this news article and provide brief reasoning in English:

Title: {title}
Content: {content[:300]}

Please provide your classification in the following format:
Importance: [1/2/3] (1=Low, 2=Normal, 3=High)
Scope: [1/2/3] (1=Limited, 2=Regional, 3=Global)
Category: [Culture/Education/Politics/Science/Economy/Society/Environment/Other]
Reasoning: [One concise sentence explaining your classification]

Keep reasoning brief and focused. Respond in English only.
"""
        
        result = self.call_ollama(prompt)
        
        importance = 2
        scope = 2
        category = "Other"
        reasoning = "No reasoning provided by model"
        
        if result:
            lines = result.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('Importance:'):
                    try:
                        importance = int(re.search(r'\d+', line).group())
                        importance = max(1, min(3, importance))
                    except:
                        pass
                elif line.startswith('Scope:'):
                    try:
                        scope = int(re.search(r'\d+', line).group())
                        scope = max(1, min(3, scope))
                    except:
                        pass
                elif line.startswith('Category:'):
                    try:
                        category = line.split(':')[1].strip()
                    except:
                        pass
                elif line.startswith('Reasoning:'):
                    try:
                        reasoning = line.split(':', 1)[1].strip()
                    except:
                        pass
        
        return importance, scope, category, reasoning

    def generate_final_report(self):
        logger.info("Final report generation started")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT title_original, title_jp, content_original, content_jp,
               source_name, url, importance, scope, category, reasoning
        FROM news_items 
        WHERE processed = TRUE
        ORDER BY importance DESC, scope DESC, category
        ''')
        
        items = cursor.fetchall()
        conn.close()
        
        if not items:
            logger.info("No items for report")
            return None
        
        total_articles = len(items)
        by_category = {}
        by_importance = {1: 0, 2: 0, 3: 0}
        
        for item in items:
            cat = item[8]
            imp = item[6]
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_importance[imp] += 1
        
        # Use Japan time zone (UTC+9)
        jst = timezone(timedelta(hours=9))
        report_date = datetime.now(jst).strftime('%Y-%m-%d %H:%M JST')
        
        markdown = f"""# World News Report

**⚠️ DISCLAIMER**: This report was generated using AI ({self.model}). AI can make mistakes, so please verify important information at your local library or through other reliable sources.

**Generated**: {report_date}  
**Total Articles**: {total_articles}  
**Classification Model**: {self.model}  
**Language**: All classifications and reasoning provided in English

## Statistics

### Category Distribution
"""
        
        for cat, count in sorted(by_category.items(), key=lambda x: x[1], reverse=True):
            markdown += f"- {cat}: {count} articles\n"
        
        markdown += "\n### Importance Distribution\n"
        for imp, count in by_importance.items():
            labels = {1: "Low", 2: "Normal", 3: "High"}
            markdown += f"- {labels[imp]}: {count} articles\n"
        
        markdown += "\n---\n\n"
        
        # Articles by category
        categorized = {}
        for item in items:
            cat = item[8]
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(item)
        
        for category, articles in sorted(categorized.items()):
            if not articles:
                continue
            
            markdown += f"# {category} ({len(articles)} articles)\n\n"
            
            for item in articles:
                (title_orig, title_jp, content_orig, content_jp,
                 source, url, importance, scope, category, reasoning) = item
                
                imp_label = {1: "Low", 2: "Normal", 3: "High"}.get(importance, "Unknown")
                scope_label = {1: "Limited", 2: "Regional", 3: "Global"}.get(scope, "Unknown")
                
                markdown += f"""## {title_jp}

**Classification**: {imp_label} | {scope_label} | {source}

### AI Analysis ({self.model})
**Reasoning**: {reasoning}

### Original Content
**{title_orig}**

{content_orig[:350]}{'...' if len(content_orig) > 350 else ''}

### Source Link
[Read Original Article]({url})

---

"""
        
        jst_str = datetime.now(jst).strftime('%Y%m%d_%H%M')
        filename = f"world_news_report_{jst_str}.md"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Final report generated: {filepath}")
        return filepath

    def run_pipeline(self):
        """Main pipeline for Qwen2.5VL classification"""
        logger.info("prototype-rss-news started (Qwen2.5VL version)")
        
        try:
            # Check environment capabilities - exit if not available
            if not self.check_environment():
                return None
            
            # 1. Collect RSS feeds
            collected = self.collect_rss_feeds()
            
            # 2. Process articles with AI classification
            processed = self.process_articles()
            
            if processed == 0:
                logger.error("No articles were processed successfully")
                return None
            
            # 3. Generate report
            report_file = self.generate_final_report()
            
            # 4. Report completion
            if report_file:
                logger.info(f"Report saved to: {report_file}")
            
            logger.info("prototype-rss-news completed successfully!")
            return {
                'collected': collected,
                'processed': processed,
                'report_file': report_file
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            return None

def main():
    """Main function for execution"""
    print("=== prototype-rss-news (Qwen2.5VL Edition) ===")
    
    # Environment check display
    ollama_check = "Available" if os.path.exists("/usr/local/bin/ollama") or os.path.exists("/usr/bin/ollama") else "Not available"
    output_dir = os.path.expanduser("~/Dropbox/rss-news-results/")
    
    print(f"Ollama: {ollama_check}")
    print(f"Model: qwen2.5vl:7b")
    print(f"Output Directory: {output_dir}")
    print(f"Features: AI Classification with Reasoning (English)")
    print()
    
    system = PrototypeRSSNews()
    result = system.run_pipeline()
    
    if result:
        print(f"Collected: {result.get('collected', 0)} articles")
        print(f"Processed: {result.get('processed', 0)} articles")
        print(f"Report: {result.get('report_file', 'None')}")
    else:
        print("Pipeline failed - check logs and ensure Ollama with qwen2.5vl:7b is running")

if __name__ == "__main__":
    main()
