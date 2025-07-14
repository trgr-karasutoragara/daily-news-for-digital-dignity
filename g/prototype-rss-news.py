#!/usr/bin/env python3
"""
prototype-rss-news - Classification Only Version
RSS Collection -> Gemma 3 1B Classification -> Gmail/MD Generation

Note: Gemma 3 1B translation is unstable, so this prototype only performs classification.
With APIs or higher-performance models, translation can also be automated.
Due to potential errors, displaying original text alongside is recommended.

Environment variable based configuration
"""

import sqlite3
import feedparser
import requests
import time
import logging
import re
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PrototypeRSSNews:
    def __init__(self, db_path="prototype_rss_news.db"):
        self.db_path = db_path
        self.ollama_url = "http://localhost:11434"
        self.model = "gemma3:1b"
        self.init_database()
        
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
            # Check if title_jp column exists
            cursor.execute("PRAGMA table_info(news_items);")
            columns = [row[1] for row in cursor.fetchall()]
            if 'title_jp' not in columns:
                logger.info("Updating database schema - adding missing columns")
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
            processed BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def check_environment(self):
        """Check available environment variables and capabilities"""
        config = {
            'gmail_available': bool(os.environ.get('GMAIL_USER') and os.environ.get('GMAIL_PASSWORD')),
            'ollama_available': False
        }
        
        # Check Ollama and Gemma 3 1B availability
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                if any('gemma3:1b' in model.get('name', '') for model in models):
                    config['ollama_available'] = True
        except:
            pass
        
        logger.info(f"Environment check: Gmail={config['gmail_available']}, Ollama+Gemma3={config['ollama_available']}")
        return config

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
                # Skip translation - only classification
                title_jp = title
                content_jp = content
                
                importance, scope, category = self.classify_article(title, content)
                
                cursor.execute('''
                UPDATE news_items 
                SET title_jp = ?, content_jp = ?, importance = ?, scope = ?, category = ?, processed = TRUE
                WHERE id = ?
                ''', (title_jp, content_jp, importance, scope, category, item_id))
                
                processed_count += 1
                logger.info(f"  Classified: {category} (Importance:{importance}, Scope:{scope})")
                time.sleep(2)  # API rate limiting
                
            except Exception as e:
                logger.error(f"Classification error ID {item_id}: {e}")
        
        conn.commit()
        conn.close()
        
        logger.info(f"Classification completed: {processed_count} items")
        return processed_count

    def classify_article(self, title, content):
        prompt = f"""
Classify this article quickly:

Title: {title}
Content: {content[:300]}

Response format:
Importance: [1/2/3]
Scope: [1/2/3]
Category: [Culture/Education/Politics/Science/Economy/Society/Environment/Other]
"""
        
        result = self.call_ollama(prompt)
        
        importance = 2
        scope = 2
        category = "Other"
        
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
        
        return importance, scope, category

    def generate_final_report(self):
        logger.info("Final report generation started")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT title_original, title_jp, content_original, content_jp,
               source_name, url, importance, scope, category
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
        
        # =============================================================================
        # TIMEZONE CONFIGURATION
        # =============================================================================
        # To change from Japan time (UTC+9) to your local timezone:
        # 
        # Method 1: Change UTC offset manually
        # Replace hours=9 with your timezone offset:
        # EST (Eastern):     timezone(timedelta(hours=-5))
        # PST (Pacific):     timezone(timedelta(hours=-8))
        # GMT (London):      timezone(timedelta(hours=0))
        # CET (Central EU):  timezone(timedelta(hours=1))
        # IST (India):       timezone(timedelta(hours=5, minutes=30))
        # CST (China):       timezone(timedelta(hours=8))
        # AEST (Australia):  timezone(timedelta(hours=10))
        #
        # Method 2: Use system local timezone (automatic)
        # Replace both lines:
        # jst = timezone(timedelta(hours=9))
        # report_date = datetime.now(jst).strftime('%Y-%m-%d %H:%M JST')
        # 
        # With:
        # local_tz = datetime.now().astimezone().tzinfo
        # report_date = datetime.now(local_tz).strftime('%Y-%m-%d %H:%M %Z')
        #
        # Method 3: Use specific timezone names (requires pytz)
        # pip install pytz
        # import pytz
        # ny_tz = pytz.timezone('America/New_York')
        # london_tz = pytz.timezone('Europe/London')
        # tokyo_tz = pytz.timezone('Asia/Tokyo')
        # report_date = datetime.now(ny_tz).strftime('%Y-%m-%d %H:%M %Z')
        # =============================================================================

        # Use Japan time zone (UTC+9)
        jst = timezone(timedelta(hours=9))
        report_date = datetime.now(jst).strftime('%Y-%m-%d %H:%M JST')
        
        markdown = f"""# World News Report

**Generated**: {report_date}  
**Total Articles**: {total_articles}  
**Classification**: {self.model}

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
                 source, url, importance, scope, category) = item
                
                imp_label = {1: "Low", 2: "Normal", 3: "High"}.get(importance, "Unknown")
                scope_label = {1: "Limited", 2: "Regional", 3: "Global"}.get(scope, "Unknown")
                
                markdown += f"""## {title_jp}

**Classification**: {imp_label} | {scope_label} | {source}

### Original
**{title_orig}**

{content_orig[:350]}{'...' if len(content_orig) > 350 else ''}

### Article Link
[Read Original]({url})

---

"""
        
        jst_str = datetime.now(jst).strftime('%Y%m%d_%H%M')
        filename = f"world_news_report_{jst_str}.md"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(markdown)
        
        logger.info(f"Final report generated: {filename}")
        return filename

    def send_gmail(self, filename):
        """Send report via Gmail if configured"""
        logger.info("Gmail sending started")
        
        gmail_user = os.environ.get('GMAIL_USER')
        gmail_password = os.environ.get('GMAIL_PASSWORD')
        
        if not gmail_user or not gmail_password:
            logger.error("Gmail environment variables not set: GMAIL_USER, GMAIL_PASSWORD")
            return False
        
        try:
            jst = timezone(timedelta(hours=9))
            current_time = datetime.now(jst).strftime('%Y/%m/%d %H:%M JST')
            
            msg = MIMEMultipart()
            msg['From'] = gmail_user
            msg['To'] = gmail_user
            msg['Subject'] = f"World News Report - {current_time}"
            
            body = f"""
World News Report is ready.

Attachment: {filename}
Classification: {self.model}
Generated: {current_time}

This is an automated message.
"""
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            if os.path.exists(filename):
                with open(filename, 'rb') as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {filename}'
                )
                msg.attach(part)
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(gmail_user, gmail_password)
            
            text = msg.as_string()
            server.sendmail(gmail_user, gmail_user, text)
            server.quit()
            
            logger.info(f"Gmail sent successfully to: {gmail_user}")
            return True
            
        except Exception as e:
            logger.error(f"Gmail sending error: {e}")
            return False

    def run_pipeline(self):
        """Main pipeline with environment-based logic"""
        logger.info("prototype-rss-news started")
        
        try:
            # Check environment capabilities
            config = self.check_environment()
            
            # 1. Collect RSS feeds
            collected = self.collect_rss_feeds()
            
            # 2. Process based on available capabilities
            processed = 0
            if config['ollama_available']:
                try:
                    processed = self.process_articles()
                    logger.info(f"Classified {processed} articles with Ollama")
                except Exception as e:
                    logger.error(f"Classification error: {e}, generating raw report")
                    # Fallback to raw data if processing fails
                    config['ollama_available'] = False
            
            if not config['ollama_available']:
                # Generate report from raw RSS data without classification
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('UPDATE news_items SET processed = TRUE, title_jp = title_original, content_jp = content_original WHERE processed = FALSE')
                conn.commit()
                conn.close()
                logger.info("Generated report from raw RSS data (no Ollama classification)")
            
            # 3. Generate report
            report_file = self.generate_final_report()
            
            # 4. Send via Gmail if configured
            email_sent = False
            if config['gmail_available'] and report_file:
                email_sent = self.send_gmail(report_file)
                logger.info(f"Email delivery: {'Success' if email_sent else 'Failed'}")
            
            # 5. Always generate local markdown file
            if report_file:
                logger.info(f"Report saved locally: {report_file}")
            
            logger.info("prototype-rss-news completed successfully!")
            return {
                'collected': collected,
                'processed': processed > 0,
                'report_file': report_file,
                'email_sent': email_sent
            }
            
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            # Try to generate at least a basic report
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute('UPDATE news_items SET processed = TRUE, title_jp = title_original, content_jp = content_original WHERE processed = FALSE')
                conn.commit()
                conn.close()
                report_file = self.generate_final_report()
                if report_file:
                    logger.info(f"Emergency report generated: {report_file}")
                    return {
                        'collected': 0,
                        'processed': False,
                        'report_file': report_file,
                        'email_sent': False
                    }
            except:
                pass
            return None

def main():
    """Main function for cron execution"""
    print("=== prototype-rss-news ===")
    
    # Environment check display
    gmail_user = os.environ.get('GMAIL_USER')
    ollama_check = "Available" if os.path.exists("/usr/local/bin/ollama") or os.path.exists("/usr/bin/ollama") else "Not available"
    
    print(f"Gmail: {'Configured - ' + gmail_user if gmail_user else 'Not configured'}")
    print(f"Ollama: {ollama_check}")
    print()
    
    system = PrototypeRSSNews()
    result = system.run_pipeline()
    
    if result:
        print(f"Collected: {result.get('collected', 0)} articles")
        print(f"Classified: {'Yes' if result.get('processed', False) else 'No (raw data)'}")
        print(f"Report: {result.get('report_file', 'None')}")
        print(f"Email: {'Sent' if result.get('email_sent', False) else 'Not sent'}")
    else:
        print("Pipeline failed - check logs")

if __name__ == "__main__":
    main()
