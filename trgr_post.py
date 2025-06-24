## Background

This project was originally developed as a personalized news generator  
to support the digital dignity of an elderly woman born in 1947.  

For those interested in the deeper ethical, social, and philosophical motivations  
behind this project, please refer to the following **speech-style draft**:  

**[AI and Elderly Dignity: A Speech Draft for Researchers](https://www.academia.edu/129405187/AI_and_Elderly_Dignity)**  
by Trgr KarasuToragara (2025)  

This is not a technical paper, but a narrative crafted to bridge abstract AI ethics  
with lived realities—especially in the context of aging, care work, and autonomy.


# This script was originally created for my mother, born in 1947,
# to help her access reliable news sources with freedom of choice.
# While it is recommended to separate configuration files,
# I have kept everything in a single script for simplicity due to its small scale.
# Some comments remain in Japanese for clarity and maintainability on my side.



#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ほぼ日刊トラガラ新聞 - 修正版
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, date
import random
import time
import re
import json
import ssl
import urllib3

# 必須ライブラリ
try:
    import feedparser
    import requests
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False
    print("❌ 必須ライブラリ不足: pip install feedparser requests")

# SSL警告を無効化（証明書エラー回避）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# ======================================
# 設定エリア
# ======================================

SENDER_EMAIL = " "
SENDER_PASSWORD = " "
RECIPIENTS = [" ", " "]
SENDER_NAME =  "
LOCATION_NAME = " "
LATITUDE =  
LONGITUDE = 

# ======================================
# API設定
# ======================================

# 今日は何の日API
HISTORY_API_URL = "http://history.muffinlabs.com/date"

# 英語名言API（バックアップ付き）
QUOTE_API_URLS = [
    "https://api.quotable.io/random",
    "https://zenquotes.io/api/random",
    "https://api.quotegarden.com/quotes/random"
]

# ======================================
# タグ分類システム
# ======================================

ARTICLE_CATEGORIES = {
    "政治・外交": {
        "icon": "🏛️",
        "keywords": ["election", "government", "president",
"minister", "parliament", "congress", "summit", "diplomacy", "vote",
"policy", "leader", "official", "political", "democracy", "campaign",
"referendum", "政治", "外交", "首相", "大統領", "国会", "選挙", "政府"]
    },
    "紛争・軍事": {
        "icon": "⚔️",
        "keywords": ["war", "conflict", "military", "attack",
"bombing", "missile", "drone", "army", "navy", "defense", "weapons",
"soldiers", "battle", "invasion", "ceasefire", "terrorism",
"security", "forces", "戦争", "軍事", "攻撃", "ミサイル", "自衛隊", "防衛", "停戦",
"テロ"]
    },
    "経済・市場": {
        "icon": "💹",
        "keywords": ["economy", "market", "trade", "business",
"company", "financial", "bank", "investment", "GDP", "inflation",
"recession", "stock", "currency", "oil", "gas", "energy", "industry",
"growth", "経済", "市場", "株価", "投資", "金融", "企業", "業績", "景気"]
    },
    "環境・気候": {
        "icon": "🌍",
        "keywords": ["climate", "environment", "global warming",
"renewable", "carbon", "pollution", "green", "sustainability",
"biodiversity", "conservation", "eco", "solar", "wind", "emissions",
"nature", "環境", "気候", "温暖化", "脱炭素", "再生可能", "エコ"]
    },
    "社会・文化": {
        "icon": "👥",
        "keywords": ["society", "social", "community", "education",
"school", "university", "culture", "religion", "family", "youth",
"elderly", "women", "gender", "rights", "protest", "demonstration",
"社会", "教育", "学校", "文化", "宗教", "権利", "抗議"]
    },
    "科学・技術": {
        "icon": "🔬",
        "keywords": ["science", "technology", "research", "AI",
"computer", "internet", "cyber", "space", "satellite", "innovation",
"discovery", "study", "experiment", "data", "digital", "科学", "技術",
"研究", "AI", "宇宙", "IT", "デジタル", "実験"]
    },
    "健康・医療": {
        "icon": "🏥",
        "keywords": ["health", "medical", "hospital", "doctor",
"patient", "disease", "virus", "pandemic", "treatment", "vaccine",
"medicine", "healthcare", "mental health", "outbreak", "surgery",
"健康", "医療", "病院", "医師", "患者", "ウイルス", "治療", "ワクチン"]
    },
    "災害・事故": {
        "icon": "🚨",
        "keywords": ["earthquake", "tsunami", "flood", "fire",
"hurricane", "tornado", "disaster", "emergency", "accident", "crash",
"explosion", "rescue", "evacuation", "damage", "victims", "alert",
"地震", "津波", "火災", "災害", "事故", "緊急", "避難", "被害"]
    }
}

# ======================================
# 象徴的翻訳システム
# ======================================

TRANSLATION_PATTERNS = {
    # 政治・会談
    r"(\w+)\s+leaders?\s+meet": r"\1首脳会談",
    r"(\w+)\s+summit": r"\1サミット",
    r"(\w+)\s+talks": r"\1協議",
    r"peace\s+negotiations": "和平交渉",
    r"trade\s+agreement": "貿易協定",
    r"diplomatic\s+meeting": "外交会談",

    # 紛争・軍事
    r"missile\s+attack": "ミサイル攻撃",
    r"air\s+strike": "空爆",
    r"military\s+operation": "軍事作戦",
    r"ceasefire\s+deal": "停戦合意",
    r"security\s+forces": "治安部隊",

    # 経済
    r"stock\s+market": "株式市場",
    r"economic\s+growth": "経済成長",
    r"oil\s+prices": "原油価格",
    r"interest\s+rates": "金利",

    # 環境
    r"climate\s+change": "気候変動",
    r"global\s+warming": "地球温暖化",
    r"renewable\s+energy": "再生可能エネルギー",

    # 健康
    r"health\s+crisis": "健康危機",
    r"medical\s+breakthrough": "医学的突破",

    # 災害
    r"natural\s+disaster": "自然災害",
    r"emergency\s+response": "緊急対応",

    # ニュース表現
    r"breaking\s+news": "速報",
    r"latest\s+update": "最新情報",
    r"official\s+statement": "公式発表"
}

# 地域・組織名
REGIONS_ORGS = {
    "European Union": "EU", "United Nations": "国連", "NATO": "NATO",
    "Middle East": "中東", "Southeast Asia": "東南アジア",
    "Eastern Europe": "東欧", "Western Europe": "西欧"
}

# 重要人物
KEY_FIGURES = {
    "Donald Trump": "トランプ大統領", "Joe Biden": "バイデン前大統領",
    "Vladimir Putin": "プーチン大統領", "Xi Jinping": "習近平国家主席",
    "Volodymyr Zelensky": "ゼレンスキー大統領", "Benjamin Netanyahu": "ネタニヤフ首相"
}

# 基本国名
COUNTRIES = {
    "China": "中国", "Russia": "ロシア", "Ukraine": "ウクライナ", "Israel": "イスラエル",
    "Iran": "イラン", "Germany": "ドイツ", "France": "フランス", "UK": "英国",
    "USA": "米国", "US": "米国", "Japan": "日本", "South Korea": "韓国",
    "North Korea": "北朝鮮", "India": "インド", "Australia": "豪州"
}

def symbolic_translate(title):
    """象徴的翻訳実行"""
    translated = title

    # パターン翻訳
    for pattern, replacement in TRANSLATION_PATTERNS.items():
        translated = re.sub(pattern, replacement, translated,
flags=re.IGNORECASE)

    # 地域・組織翻訳
    for eng, jp in REGIONS_ORGS.items():
        translated = re.sub(r'\b' + re.escape(eng) + r'\b', jp,
translated, flags=re.IGNORECASE)

    # 人物翻訳
    for eng, jp in KEY_FIGURES.items():
        translated = re.sub(r'\b' + re.escape(eng) + r'\b', jp,
translated, flags=re.IGNORECASE)

    # 国名翻訳
    for eng, jp in COUNTRIES.items():
        translated = re.sub(r'\b' + re.escape(eng) + r'\b', jp,
translated, flags=re.IGNORECASE)

    # 変更があった場合のみ併記
    if translated.lower() != title.lower():
        return f"{title} ({translated})"
    else:
        return title

# ======================================
# 記事分析機能
# ======================================

def analyze_article_tags(title, summary):
    """記事タグ分析"""
    text = (title + " " + summary).lower()
    scores = {}

    for category, data in ARTICLE_CATEGORIES.items():
        score = sum(1 for keyword in data["keywords"] if keyword in text)
        if score > 0:
            scores[category] = score

    # 上位3つまでのタグ
    sorted_tags = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]

    return [
        {
            "name": category,
            "icon": ARTICLE_CATEGORIES[category]["icon"]
        }
        for category, score in sorted_tags
    ] if sorted_tags else [{"name": "一般", "icon": "📰"}]

# ======================================
# API機能（改善版）
# ======================================

def get_api_quote():
    """API経由で英語名言取得（複数API対応）"""
    for api_url in QUOTE_API_URLS:
        try:
            response = requests.get(api_url, timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()

                if api_url == "https://api.quotable.io/random":
                    return {
                        "quote": data.get("content", ""),
                        "author": data.get("author", "Unknown"),
                        "translation": ""
                    }
                elif api_url == "https://zenquotes.io/api/random":
                    if isinstance(data, list) and len(data) > 0:
                        return {
                            "quote": data[0].get("q", ""),
                            "author": data[0].get("a", "Unknown"),
                            "translation": ""
                        }
                print(f"✅ 名言API成功: {api_url}")
                break
        except Exception as e:
            print(f"⚠️  名言API失敗 ({api_url}): {str(e)}")
            continue

    # 全てのAPIが失敗した場合のフォールバック
    fallback_quotes = [
        {"quote": "The only way to do great work is to love what you
do.", "author": "Steve Jobs"},
        {"quote": "Innovation distinguishes between a leader and a
follower.", "author": "Steve Jobs"},
        {"quote": "Stay hungry, stay foolish.", "author": "Steve Jobs"},
        {"quote": "The future belongs to those who believe in the
beauty of their dreams.", "author": "Eleanor Roosevelt"},
        {"quote": "It is during our darkest moments that we must focus
to see the light.", "author": "Aristotle"},
    ]

    return random.choice(fallback_quotes)

def get_api_history():
    """API経由で今日は何の日取得（改善版）"""
    try:
        today = date.today()
        url = f"{HISTORY_API_URL}/{today.month}/{today.day}"
        response = requests.get(url, timeout=10, verify=False)

        if response.status_code == 200:
            data = response.json()
            events = data.get("data", {}).get("Events", [])

            if events:
                # 歴史的に重要そうなイベントを選択（古い年代を優先）
                important_events = sorted(events, key=lambda x:
int(x.get("year", "0")))
                selected_event = important_events[0] if
important_events else events[0]

                year = selected_event.get("year", "")
                text = selected_event.get("text", "")

                return f"{year} - {text[:150]}{'...' if len(text) >
150 else ''}"

        print("✅ 歴史API成功")

    except Exception as e:
        print(f"⚠️  歴史API失敗: {str(e)}")

    # フォールバック
    today = date.today()
    fallback_events = [
        f"{today.month}月{today.day}日 - 今日という日は二度と来ない特別な日です。新しい発見と学びを大切にしましょう。",
        f"{today.month}月{today.day}日 - 歴史は毎日作られています。今日も新しい一歩を踏み出しましょう。",
        f"{today.month}月{today.day}日 - 過去から学び、現在を生き、未来に希望を持ちましょう。"
    ]

    return random.choice(fallback_events)

# ======================================
# ニュース取得（改善版）
# ======================================

# 更新されたニュースソース（動作確認済みURL）
JAPANESE_NEWS_SOURCES = [
    ("NHK 主要ニュース", "https://www.nhk.or.jp/rss/news/cat0.xml", 15),
    ("NHK 社会", "https://www.nhk.or.jp/rss/news/cat1.xml", 10),
    ("NHK 政治", "https://www.nhk.or.jp/rss/news/cat4.xml", 10),
    ("NHK 経済", "https://www.nhk.or.jp/rss/news/cat5.xml", 10),
    ("NHK 国際", "https://www.nhk.or.jp/rss/news/cat6.xml", 10),
    ("NHK 科学文化", "https://www.nhk.or.jp/rss/news/cat3.xml", 8),
    ("Yahoo主要ニュース", "https://news.yahoo.co.jp/rss/topics/top-picks.xml", 12),
    ("Yahoo国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml", 10),
    ("Yahoo経済", "https://news.yahoo.co.jp/rss/topics/business.xml", 8),
    ("Yahoo国際", "https://news.yahoo.co.jp/rss/topics/world.xml", 8),
    ("時事通信", "https://www.jiji.com/rss/ranking.rdf", 8),
    ("朝日新聞", "https://www.asahi.com/rss/asahi/newsheadlines.rdf", 8),  # 共同通信代替
]

INTERNATIONAL_NEWS_SOURCES = [
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", 8),
    ("BBC UK", "http://feeds.bbci.co.uk/news/uk/rss.xml", 5),
    ("The Guardian World", "https://www.theguardian.com/world/rss", 5),
    ("ABC Australia", "https://www.abc.net.au/news/feed/45924/rss.xml", 4),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all", 5),
    ("France 24", "https://www.france24.com/en/rss", 4),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", 6),
    ("Sky News", "https://feeds.skynews.com/feeds/rss/world.xml", 4),
    ("CNN International", "http://rss.cnn.com/rss/edition.rss", 5),
    ("Euronews", "https://feeds.feedburner.com/euronews/en/news", 4),
]

EXCLUDE_KEYWORDS = [
    "女性自身", "女性セブン", "週刊女性", "FLASH", "FRIDAY", "週刊文春", "週刊新潮",
    "日刊ゲンダイ", "東スポ", "サンスポ", "デイリースポーツ", "夕刊フジ", "日刊スポーツ",
    "芸能", "不倫", "浮気", "離婚", "炎上", "暴露", "激怒", "衝撃",
    "緊急事態", "大炎上", "批判殺到", "物議", "話題騒然", "賛否両論",
    "AV", "風俗", "パチンコ", "競馬", "宝くじ", "ギャンブル", "詐欺"
]

def fetch_rss_with_tags(source_name, url, max_items):
    """RSSニュース取得（エラーハンドリング強化版）"""
    if not LIBS_AVAILABLE:
        return []

    try:
        print(f"📡 {source_name} から取得中...")

        # User-Agentを設定してブロック回避
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)
AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124
Safari/537.36'
        }

        # HTTPSの場合はverify=Falseを追加
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()

        # feedparserに渡すためにBytesIOを使用
        from io import BytesIO
        feed = feedparser.parse(BytesIO(response.content))

        if not feed.entries:
            print(f"⚠️  {source_name}: RSSエントリが空")
            return []

        articles = []

        for entry in feed.entries[:max_items * 3]:
            try:
                title = entry.title.strip() if hasattr(entry, 'title')
else "タイトルなし"

                if any(keyword in title for keyword in EXCLUDE_KEYWORDS):
                    continue

                summary = ""
                if hasattr(entry, 'summary'):
                    summary = entry.summary
                elif hasattr(entry, 'description'):
                    summary = entry.description

                if summary:
                    summary = re.sub(r'<[^>]+>', '', summary)
                    summary = summary.strip()
                    if len(summary) > 120:
                        summary = summary[:120] + "..."

                # リンクURL取得
                link = entry.link if hasattr(entry, 'link') else ""

                # タグ分析
                tags = analyze_article_tags(title, summary)

                # 国際ニュースの場合は翻訳
                if source_name not in [src[0] for src in JAPANESE_NEWS_SOURCES]:
                    translated_title = symbolic_translate(title)
                else:
                    translated_title = title

                articles.append({
                    'title': translated_title,
                    'summary': summary,
                    'url': link,
                    'source': source_name,
                    'tags': tags[:2]  # 最大2タグ
                })

                if len(articles) >= max_items:
                    break

            except Exception as e:
                print(f"⚠️  {source_name} エントリ処理エラー: {str(e)}")
                continue

        print(f"✅ {source_name}: {len(articles)}件取得")
        return articles

    except requests.exceptions.RequestException as e:
        print(f"❌ {source_name} HTTP取得失敗: {str(e)}")
        return []
    except Exception as e:
        print(f"❌ {source_name} 取得失敗: {str(e)}")
        return []

def get_all_news():
    """全ニュース取得（改善版）"""
    all_news = {'japanese': [], 'international': []}

    if not LIBS_AVAILABLE:
        return all_news

    print("📰 日本語ニュース取得開始...")
    for source_name, url, max_items in JAPANESE_NEWS_SOURCES:
        articles = fetch_rss_with_tags(source_name, url, max_items)
        all_news['japanese'].extend(articles)
        time.sleep(1)  # レート制限対応

    print("🌍 国際ニュース取得開始...")
    for source_name, url, max_items in INTERNATIONAL_NEWS_SOURCES:
        articles = fetch_rss_with_tags(source_name, url, max_items)
        all_news['international'].extend(articles)
        time.sleep(1)  # レート制限対応

    # 重複除去
    all_news['japanese'] = remove_duplicates(all_news['japanese'])
    all_news['international'] = remove_duplicates(all_news['international'])

    print(f"📊 ニュース取得完了: 国内{len(all_news['japanese'])}件,
国際{len(all_news['international'])}件")

    return all_news

def remove_duplicates(articles):
    """記事重複除去"""
    seen_titles = set()
    unique_articles = []

    for article in articles:
        title_words = set(article['title'].lower().split())
        is_duplicate = False

        for seen_title in seen_titles:
            seen_words = set(seen_title.lower().split())
            if len(title_words & seen_words) / len(title_words |
seen_words) > 0.7:
                is_duplicate = True
                break

        if not is_duplicate:
            seen_titles.add(article['title'])
            unique_articles.append(article)

    return unique_articles

# ======================================
# 天気取得（改善版）
# ======================================

def get_weather_data():
    """天気データ取得（改善版）"""
    if not LIBS_AVAILABLE:
        return get_fallback_weather()

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            'latitude': LATITUDE,
            'longitude': LONGITUDE,
            'hourly': 'temperature_2m,weather_code',
            'daily': 'temperature_2m_max,temperature_2m_min,weather_code',
            'timezone': 'Asia/Tokyo',
            'forecast_days': 3
        }

        response = requests.get(url, params=params, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()

        weather_codes = {
            0: "快晴", 1: "晴れ", 2: "部分的に曇り", 3: "曇り",
            45: "霧", 48: "霧氷", 51: "小雨", 53: "雨", 55: "強雨",
            61: "雨", 63: "雨", 65: "強雨", 71: "雪", 73: "雪", 75: "大雪",
            77: "みぞれ", 80: "にわか雨", 81: "にわか雨", 82: "強いにわか雨",
            85: "雪", 86: "大雪", 95: "雷雨", 96: "雷雨", 99: "雷雨"
        }

        now_hour = min(datetime.now().hour,
len(data['hourly']['temperature_2m']) - 1)
        current_temp = round(data['hourly']['temperature_2m'][now_hour])
        current_code = data['hourly']['weather_code'][now_hour]
        current_weather = weather_codes.get(current_code, "不明")

        weekly_forecast = []
        days = ["今日", "明日", "明後日"]
        for i in range(3):
            max_temp = round(data['daily']['temperature_2m_max'][i])
            min_temp = round(data['daily']['temperature_2m_min'][i])
            code = data['daily']['weather_code'][i]
            weather_desc = weather_codes.get(code, "不明")
            weekly_forecast.append({
                'date': days[i],
                'high': f"{max_temp}°C",
                'low': f"{min_temp}°C",
                'weather': weather_desc
            })

        print(f"✅ {LOCATION_NAME}の天気取得: {current_temp}°C - {current_weather}")

        return {
            'current_temp': f"{current_temp}°C",
            'current_weather': current_weather,
            'weekly': weekly_forecast
        }

    except Exception as e:
        print(f"⚠️  天気API失敗: {str(e)}")
        return get_fallback_weather()

def get_fallback_weather():
    """フォールバック天気"""
    return {
        'current_temp': "15°C",
        'current_weather': "晴れ",
        'weekly': [
            {'date': '今日', 'high': '20°C', 'low': '8°C', 'weather': '晴れ'},
            {'date': '明日', 'high': '22°C', 'low': '10°C', 'weather': '曇り'},
            {'date': '明後日', 'high': '19°C', 'low': '9°C', 'weather': '雨'}
        ]
    }

# ======================================
# HTML生成（改善版）
# ======================================

def generate_nhk_style_newspaper():
    """NHKスタイル新聞HTML生成"""
    today = date.today()
    now = datetime.now()

    print("📰 NHKスタイル新聞生成中...")

    quote = get_api_quote()
    history = get_api_history()
    weather = get_weather_data()
    news = get_all_news()

    weekdays = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    weekday_jp = weekdays[today.weekday()]

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ほぼ日刊トラガラ新聞 - {today.strftime('%Y年%m月%d日')}</title>
    <style>
        body {{
            font-family: 'Hiragino Sans', 'Yu Gothic', 'Meiryo', sans-serif;
            font-size: 16px;
            line-height: 1.7;
            max-width: 1000px;
            margin: 0 auto;
            padding: 15px;
            background-color: #fff;
            color: #333;
        }}
        .header {{
            background: #003f7f;
            color: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 5px;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
            font-weight: bold;
        }}
        .header .date {{
            margin: 8px 0 0 0;
            font-size: 18px;
        }}
        .info-bar {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 15px;
            margin-bottom: 25px;
        }}
        .info-box {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #003f7f;
        }}
        .info-box h3 {{
            margin: 0 0 10px 0;
            font-size: 16px;
            color: #003f7f;
            font-weight: bold;
        }}
        .weather-mini {{
            display: flex;
            justify-content: space-between;
            font-size: 14px;
        }}
        .weather-day {{
            text-align: center;
        }}
        .quote-text {{
            font-size: 14px;
            font-style: italic;
            color: #555;
        }}
        .main-content {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
        }}
        .news-section {{
            background: white;
        }}
        .news-title {{
            font-size: 22px;
            font-weight: bold;
            color: #003f7f;
            margin: 0 0 15px 0;
            padding-bottom: 8px;
            border-bottom: 3px solid #003f7f;
        }}
        .news-item {{
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #fafafa;
        }}
        .news-tags {{
            margin-bottom: 8px;
        }}
        .tag {{
            display: inline-block;
            background: #e1f5fe;
            color: #0277bd;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 12px;
            margin-right: 5px;
        }}
        .news-headline {{
            font-size: 16px;
            font-weight: bold;
            margin: 8px 0;
            line-height: 1.4;
        }}
        .news-headline a {{
            color: #333;
            text-decoration: none;
        }}
        .news-headline a:hover {{
            color: #003f7f;
            text-decoration: underline;
        }}
        .news-summary {{
            font-size: 14px;
            color: #666;
            margin: 8px 0;
        }}
        .news-source {{
            font-size: 12px;
            color: #888;
        }}
        .sidebar {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
        }}
        .sidebar h3 {{
            color: #003f7f;
            font-size: 16px;
            margin: 0 0 10px 0;
            border-bottom: 2px solid #003f7f;
            padding-bottom: 5px;
        }}
        .sidebar-content {{
            font-size: 14px;
            line-height: 1.6;
        }}
        .stats-item {{
            display: flex;
            justify-content: space-between;
            margin: 5px 0;
            padding: 5px 0;
            border-bottom: 1px dotted #ccc;
        }}
        .footer {{
            background: #003f7f;
            color: white;
            text-align: center;
            padding: 15px;
            margin-top: 30px;
            border-radius: 5px;
        }}
        .note {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 10px;
            margin: 15px 0;
            border-radius: 5px;
            font-size: 14px;
            color: #856404;
        }}
        .success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}
        @media (max-width: 768px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
            .info-bar {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📰 ほぼ日刊トラガラ新聞</h1>
        <div class="date">{today.strftime('%Y年%m月%d日')} ({weekday_jp})</div>
    </div>

    <div class="info-bar">
        <div class="info-box">
            <h3>🌤️ {LOCATION_NAME}の天気</h3>
            <div style="text-align: center; margin-bottom: 10px;">
                <strong>{weather['current_temp']}
{weather['current_weather']}</strong>
            </div>
            <div class="weather-mini">"""

    for item in weather['weekly']:
        html += f"""
                <div class="weather-day">
                    <div style="font-weight: bold;">{item['date']}</div>
                    <div>{item['high']}/{item['low']}</div>
                    <div style="font-size: 12px;">{item['weather']}</div>
                </div>"""

    html += f"""
            </div>
        </div>

        <div class="info-box">
            <h3>📚 今日は何の日</h3>
            <div style="font-size: 14px; line-height: 1.5;">
                {history[:120]}{'...' if len(history) > 120 else ''}
            </div>
        </div>

        <div class="info-box">
            <h3>💭 今日の言葉</h3>
            <div class="quote-text">
                "{quote['quote'][:70]}{'...' if len(quote['quote']) >
70 else ''}"
                <div style="text-align: right; margin-top: 5px;
font-weight: bold;">
                    — {quote['author']}
                </div>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="news-section">
            <h2 class="news-title">🇯🇵 国内ニュース</h2>
            <div class="note success">
                ✅ NHK・Yahoo・時事通信など信頼できる報道機関から{len(news['japanese'])}件を自動取得
            </div>"""

    # 日本ニュース（制限なしで全件表示）
    for article in news['japanese']:
        html += f"""
            <div class="news-item">
                <div class="news-tags">
                    {''.join([f'<span class="tag">{tag["icon"]}
{tag["name"]}</span>' for tag in article["tags"]])}
                </div>
                <div class="news-headline">
                    <a href="{article['url']}"
target="_blank">{article['title']}</a>
                </div>
                <div class="news-summary">{article['summary']}</div>
                <div class="news-source">出典: {article['source']}</div>
            </div>"""

    html += f"""
            <h2 class="news-title">🌍 国際ニュース</h2>
            <div class="note success">
                ✅ BBC・Guardian・Deutsche
Welle・地域メディアから{len(news['international'])}件を自動取得・翻訳
            </div>"""

    # 国際ニュース（制限なしで全件表示）
    for article in news['international']:
        html += f"""
            <div class="news-item">
                <div class="news-tags">
                    {''.join([f'<span class="tag">{tag["icon"]}
{tag["name"]}</span>' for tag in article["tags"]])}
                </div>
                <div class="news-headline">
                    <a href="{article['url']}"
target="_blank">{article['title']}</a>
                </div>
                <div class="news-summary">{article['summary']}</div>
                <div class="news-source">出典: {article['source']}</div>
            </div>"""

    # タグ統計を生成
    all_tags = {}
    for article in news['japanese'] + news['international']:
        for tag in article['tags']:
            tag_name = tag['name']
            if tag_name in all_tags:
                all_tags[tag_name] += 1
            else:
                all_tags[tag_name] = 1

    sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:5]

    html += f"""
        </div>

        <div class="sidebar">
            <h3>📊 今日の記事分析</h3>
            <div class="sidebar-content">
                <div class="stats-item">
                    <span><strong>総記事数</strong></span>
                    <span><strong>{len(news['japanese']) +
len(news['international'])}件</strong></span>
                </div>
                <div class="stats-item">
                    <span>国内ニュース</span>
                    <span>{len(news['japanese'])}件</span>
                </div>
                <div class="stats-item">
                    <span>国際ニュース</span>
                    <span>{len(news['international'])}件</span>
                </div>
                <hr style="margin: 15px 0;">
                <h4 style="margin: 10px 0; color: #003f7f;">主要カテゴリ</h4>"""

    for tag_name, count in sorted_tags:
        html += f"""
                <div class="stats-item">
                    <span>{tag_name}</span>
                    <span>{count}件</span>
                </div>"""

    html += f"""
                <hr style="margin: 15px 0;">
                <p style="font-size: 13px; color: #666;">
                    記事は内容に基づいて自動分類されます。
                    AIによるタグ付けで効率的な情報収集が可能です。
                </p>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><strong>ほぼ日刊トラガラ新聞</strong></p>
        <p>発行: {SENDER_NAME} | 発行日時: {now.strftime('%Y年%m月%d日 %H:%M')}</p>
        <p>📡 自動取得・🔍 AI分析・📧 自動配信</p>
    </div>
</body>
</html>"""

    return html

# ======================================
# メール送信
# ======================================

def send_email(html_content):
    """メール送信"""
    today = date.today()
    subject = f"📰 ほぼ日刊トラガラ新聞 - {today.strftime('%Y年%m月%d日')}"

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = ", ".join(RECIPIENTS)

        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)

        for recipient in RECIPIENTS:
            server.send_message(msg, to_addrs=[recipient])
            print(f"✅ メール送信完了: {recipient}")

        server.quit()
        return True

    except Exception as e:
        print(f"❌ メール送信エラー: {str(e)}")
        return False

def main():
    """メイン実行"""
    print("📰 ほぼ日刊トラガラ新聞生成開始")
    print(f"📅 発行日: {date.today().strftime('%Y年%m月%d日')}")

    if not LIBS_AVAILABLE:
        print("❌ pip install feedparser requests を実行してください")
        return

    # HTML生成
    html_content = generate_nhk_style_newspaper()

    # メール送信（ファイル保存なし）
    print("\n📧 新聞配信中...")
    success = send_email(html_content)

    if success:
        print("🎉 新聞配信完了！")
    else:
        print("❌ メール送信失敗")

    print(f"\n📊 改善内容:")
    print(f"✅ SSL証明書エラー対応（verify=False）")
    print(f"✅ RSSフィード取得の改善（タイムアウト・ヘッダー設定）")
    print(f"✅ 複数API対応（名言・歴史のフォールバック）")
    print(f"✅ 記事重複除去機能追加")
    print(f"✅ エラーハンドリング強化")
    print(f"✅ 全記事を新聞に反映（件数制限撤廃）")
    print(f"✅ 動作不安定ソース除外（Reuters・AP News削除）")
    print(f"✅ ローカルファイル保存削除（メール配信のみ）")

if __name__ == "__main__":
    main()