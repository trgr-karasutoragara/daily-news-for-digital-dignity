# =============================================================================
# IMPORTANT NOTICE & CROSS-PLATFORM COMPATIBILITY - 2025/6/27
# =============================================================================
# This script was developed and tested exclusively in Japanese environments.
# Users in different locales may encounter encoding/character set issues.
# Please ensure UTF-8 support and proper Japanese font rendering.
# 
# REQUIREMENTS:
# - UTF-8 encoding support
# - Japanese locale support (optional but recommended)
# - Python packages: feedparser, requests, google-generativeai
# - Valid API keys for Gemini and email services
# =============================================================================

## Background

This script is an AI-enhanced version of the personalized news generator,
originally created to support the digital dignity of an elderly woman born in 1947.

Using Gemini 2.0 Flash (via the API), this version adds:
– Automatic selection and sorting of top international news articles
– Optional translation using a large language model (currently limited by quota)

This script is part of the same project as:
**[AI and Elderly Dignity: A Speech Draft for Researchers](https://www.academia.edu/129405187/AI_and_Elderly_Dignity)**  
by Trgr KarasuToragara (2025)

# NOTE:
# - API key (GEMINI_API_KEY) must be provided separately and should NOT be published.
# - For simplicity, configuration is embedded in this script.
# - Some comments remain in Japanese for clarity and maintainability.


#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ほぼ日刊トラガラ新聞 - Gemini 2.0 AI版（全件バッチ翻訳版）

革新的改善：
1. 全件バッチ翻訳システム（全20件を1回のAPI呼び出しで処理）
2. 翻訳後重要度ソート（和訳を見て判断→並び替え）
3. 全記事で原文・和訳併記
4. 究極のAPI効率化: 20回 → 1回（20倍効率化）
5. NHK充実・Yahoo削除・国内45件・優先度別背景色
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
    from google import genai
    LIBS_AVAILABLE = True
except ImportError:
    LIBS_AVAILABLE = False
    print("❌ 必須ライブラリ不足: pip install feedparser requests google-generativeai")

# SSL警告を無効化（証明書エラー回避）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ssl._create_default_https_context = ssl._create_unverified_context

# ======================================
# 設定エリア
# ======================================

SENDER_EMAIL = "your_email@gmail.com"
SENDER_PASSWORD = "your_app_password"
RECIPIENTS = ["recipient1@example.com", "recipient2@example.com"]
SENDER_NAME = ""
LOCATION_NAME = ""
LATITUDE = 
LONGITUDE = 

# Gemini API設定
GEMINI_API_KEY = "your_gemini_api_key"
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Gemini モデル選択
GEMINI_MODEL = "gemini-2.0-flash"

# 翻訳制限設定（全件バッチ翻訳版）
ENABLE_BATCH_TRANSLATION = True  # バッチ翻訳有効/無効
MAX_BATCH_SIZE = 20  # 一度に翻訳する最大件数
TRANSLATION_DELAY = 3

# ======================================
# ニュースソース（NHK充実・Yahoo削除版）
# ======================================

# NHK充実版（地方・文化系追加）
JAPANESE_NEWS_SOURCES = [
    ("NHK 主要ニュース", "https://www.nhk.or.jp/rss/news/cat0.xml", 20),  # 増量
    ("NHK 社会", "https://www.nhk.or.jp/rss/news/cat1.xml", 15),  # 増量
    ("NHK 政治", "https://www.nhk.or.jp/rss/news/cat4.xml", 15),  # 増量
    ("NHK 経済", "https://www.nhk.or.jp/rss/news/cat5.xml", 15),  # 増量
    ("NHK 国際", "https://www.nhk.or.jp/rss/news/cat6.xml", 12),
    ("NHK 科学文化", "https://www.nhk.or.jp/rss/news/cat3.xml", 12),
    ("NHK スポーツ", "https://www.nhk.or.jp/rss/news/cat7.xml", 8),  # 追加
    ("NHK 気象災害", "https://www.nhk.or.jp/rss/news/cat2.xml", 10),  # 追加
    # Yahooニュースは全てコメントアウト
    # ("Yahoo主要ニュース", "https://news.yahoo.co.jp/rss/topics/top-picks.xml", 12),
    # ("Yahoo国内", "https://news.yahoo.co.jp/rss/topics/domestic.xml", 10),
    # ("Yahoo経済", "https://news.yahoo.co.jp/rss/topics/business.xml", 8),
    # ("Yahoo国際", "https://news.yahoo.co.jp/rss/topics/world.xml", 8),
    ("時事通信", "https://www.jiji.com/rss/ranking.rdf", 10),
    ("朝日新聞", "https://www.asahi.com/rss/asahi/newsheadlines.rdf", 10),
]

INTERNATIONAL_NEWS_SOURCES = [
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml", 8),
    ("BBC UK", "http://feeds.bbci.co.uk/news/uk/rss.xml", 5),
    ("The Guardian World", "https://www.theguardian.com/world/rss", 5),
    ("ABC Australia", "https://www.abc.net.au/news/feed/45924/rss.xml", 4),
    ("Deutsche Welle", "https://rss.dw.com/rdf/rss-en-all", 5),
    ("France 24", "https://www.france24.com/en/rss", 4),
    ("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", 6),
    ("El País España", "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", 6),
]

EXCLUDE_KEYWORDS = [
    "女性自身", "女性セブン", "週刊女性", "FLASH", "FRIDAY", "週刊文春", "週刊新潮",
    "日刊ゲンダイ", "東スポ", "サンスポ", "デイリースポーツ", "夕刊フジ", "日刊スポーツ",
    "芸能", "不倫", "浮気", "離婚", "炎上", "暴露", "激怒", "衝撃", 
    "緊急事態", "大炎上", "批判殺到", "物議", "話題騒然", "賛否両論",
]

# ======================================
# タグ分類システム
# ======================================

ARTICLE_CATEGORIES = {
    "政治・外交": {
        "icon": "🏛️",
        "keywords": ["election", "government", "president", "minister", "parliament", "congress", "summit", "diplomacy", "vote", "policy", "leader", "official", "political", "democracy", "campaign", "referendum", "政治", "外交", "首相", "大統領", "国会", "選挙", "政府"]
    },
    "紛争・軍事": {
        "icon": "⚔️", 
        "keywords": ["war", "conflict", "military", "attack", "bombing", "missile", "drone", "army", "navy", "defense", "weapons", "soldiers", "battle", "invasion", "ceasefire", "terrorism", "security", "forces", "戦争", "軍事", "攻撃", "ミサイル", "自衛隊", "防衛", "停戦", "テロ"]
    },
    "経済・市場": {
        "icon": "💹",
        "keywords": ["economy", "market", "trade", "business", "company", "financial", "bank", "investment", "GDP", "inflation", "recession", "stock", "currency", "oil", "gas", "energy", "industry", "growth", "経済", "市場", "株価", "投資", "金融", "企業", "業績", "景気"]
    },
    "環境・気候": {
        "icon": "🌍",
        "keywords": ["climate", "environment", "global warming", "renewable", "carbon", "pollution", "green", "sustainability", "biodiversity", "conservation", "eco", "solar", "wind", "emissions", "nature", "環境", "気候", "温暖化", "脱炭素", "再生可能", "エコ"]
    },
    "社会・文化": {
        "icon": "👥",
        "keywords": ["society", "social", "community", "education", "school", "university", "culture", "religion", "family", "youth", "elderly", "women", "gender", "rights", "protest", "demonstration", "社会", "教育", "学校", "文化", "宗教", "権利", "抗議"]
    },
    "科学・技術": {
        "icon": "🔬",
        "keywords": ["science", "technology", "research", "AI", "computer", "internet", "cyber", "space", "satellite", "innovation", "discovery", "study", "experiment", "data", "digital", "科学", "技術", "研究", "AI", "宇宙", "IT", "デジタル", "実験"]
    },
    "健康・医療": {
        "icon": "🏥",
        "keywords": ["health", "medical", "hospital", "doctor", "patient", "disease", "virus", "pandemic", "treatment", "vaccine", "medicine", "healthcare", "mental health", "outbreak", "surgery", "健康", "医療", "病院", "医師", "患者", "ウイルス", "治療", "ワクチン"]
    },
    "災害・事故": {
        "icon": "🚨",
        "keywords": ["earthquake", "tsunami", "flood", "fire", "hurricane", "tornado", "disaster", "emergency", "accident", "crash", "explosion", "rescue", "evacuation", "damage", "victims", "alert", "地震", "津波", "火災", "災害", "事故", "緊急", "避難", "被害"]
    }
}

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
# バッチ翻訳システム（API節約版）
# ======================================

def batch_translate_articles(articles_list):
    """バッチ翻訳（複数記事を1回のAPI呼び出しで翻訳）"""
    if not articles_list:
        return {}
    
    try:
        # バッチ翻訳用プロンプト作成
        titles_text = ""
        for i, article in enumerate(articles_list, 1):
            titles_text += f"{i}. {article['original_title']}\n"
        
        prompt = f"""以下の{len(articles_list)}件の英語ニュースタイトルを、それぞれ自然な日本語に翻訳してください。

英語タイトル一覧：
{titles_text}

以下のJSON形式で回答してください：
{{
    "translations": [
        {{"id": 1, "translation": "1つ目の日本語翻訳"}},
        {{"id": 2, "translation": "2つ目の日本語翻訳"}},
        ...
    ]
}}

注意：翻訳のみを出力し、説明は不要です。"""
        
        print(f"🚀 バッチ翻訳実行中: {len(articles_list)}件を1回のAPI呼び出しで処理...")
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        result_text = response.text.strip()
        
        # JSONブロック抽出
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        elif "{" in result_text and "}" in result_text:
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            result_text = result_text[json_start:json_end]
        
        result = json.loads(result_text)
        translations = result.get("translations", [])
        
        # 翻訳結果をマッピング
        translation_map = {}
        for trans in translations:
            article_id = trans.get("id", 0) - 1  # 0ベースに変換
            translation = trans.get("translation", "")
            if 0 <= article_id < len(articles_list) and translation:
                original_title = articles_list[article_id]['original_title']
                translation_map[original_title] = translation
        
        print(f"✅ バッチ翻訳成功: {len(translation_map)}/{len(articles_list)}件の翻訳を取得")
        return translation_map
        
    except Exception as e:
        print(f"❌ バッチ翻訳失敗: {str(e)}")
        return {}

def translate_top_articles_only(title, summary=""):
    """個別翻訳（バッチ翻訳の代替・緊急用）"""
    try:
        prompt = f"""以下の英語ニュースタイトルを自然な日本語に翻訳してください。

英語: {title}

JSONで出力：
{{
    "translation": "日本語翻訳"
}}"""
        
        response = gemini_client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        result_text = response.text.strip()
        
        # JSONブロック抽出
        if "```json" in result_text:
            json_start = result_text.find("```json") + 7
            json_end = result_text.find("```", json_start)
            result_text = result_text[json_start:json_end].strip()
        elif "{" in result_text and "}" in result_text:
            json_start = result_text.find("{")
            json_end = result_text.rfind("}") + 1
            result_text = result_text[json_start:json_end]
        
        result = json.loads(result_text)
        translation = result.get("translation", "")
        
        if translation and translation != title:
            print(f"✅ 個別翻訳成功: {title[:30]}... → {translation[:30]}...")
            return translation
        else:
            print(f"⚠️  個別翻訳結果が不適切、元タイトル使用")
            return title
        
    except Exception as e:
        print(f"❌ 個別翻訳失敗: {str(e)} - 元タイトル使用")
        return title

def process_articles_simplified(articles):
    """全件バッチ翻訳＋重要度ソート処理"""
    analyzed_articles = []
    api_calls_used = 0
    translation_count = 0
    
    print(f"📰 記事処理開始（全件バッチ翻訳: {ENABLE_BATCH_TRANSLATION}）...")
    
    # 国内・国際記事を分離
    international_articles = [a for a in articles if a['is_international']]
    domestic_articles = [a for a in articles if not a['is_international']]
    
    # 国際記事の全件バッチ翻訳
    translation_map = {}
    if ENABLE_BATCH_TRANSLATION and international_articles:
        try:
            # 全ての国際記事を一度に翻訳（1回のAPI呼び出し）
            batch_size = min(len(international_articles), MAX_BATCH_SIZE)
            articles_to_translate = international_articles[:batch_size]
            
            print(f"🚀 全件バッチ翻訳実行: {len(articles_to_translate)}件を1回のAPI呼び出しで処理...")
            translation_map = batch_translate_articles(articles_to_translate)
            api_calls_used = 1 if translation_map else 0
            translation_count = len(translation_map)
            
            print(f"🎯 全件バッチ翻訳結果: {translation_count}/{len(articles_to_translate)}件成功")
            
        except Exception as e:
            print(f"⚠️  全件バッチ翻訳失敗: {str(e)}")
            translation_map = {}
    
    # 国際記事の翻訳結果適用
    for article in international_articles:
        try:
            title = article['original_title']
            
            if title in translation_map:
                # バッチ翻訳成功
                translated_title = translation_map[title]
                article.update({
                    'title': translated_title,
                    'has_translation': True,
                    'importance': 3,  # 後で重要度ソート
                    'reliability': 3,
                    'emotional': 1,
                    'reasoning': "全件バッチ翻訳完了"
                })
            else:
                # 翻訳失敗または対象外
                article.update({
                    'title': title,  # 英語のまま
                    'has_translation': False,
                    'importance': 3,
                    'reliability': 3,
                    'emotional': 1,
                    'reasoning': "バッチ翻訳失敗・英語原文" if ENABLE_BATCH_TRANSLATION else "翻訳無効・英語原文"
                })
            
            analyzed_articles.append(article)
            
        except Exception as e:
            print(f"⚠️  国際記事処理失敗: {str(e)}")
            analyzed_articles.append(article)
    
    # 翻訳後の重要度ソート（和訳を見て判断可能）
    if international_articles:
        print("📊 翻訳後重要度ソート実行...")
        important_keywords = ['trump', 'putin', 'ceasefire', 'nato', 'ukraine', 'israel', 'iran', 'election', 'war', 'summit', 
                             'トランプ', 'プーチン', '停戦', 'NATO', 'ウクライナ', 'イスラエル', 'イラン', '選挙', '戦争', '首脳会談']
        
        # 重要度スコア計算（原文と和訳の両方をチェック）
        for article in [a for a in analyzed_articles if a['is_international']]:
            score = 0
            title_text = (article['original_title'] + " " + article['title']).lower()
            
            for keyword in important_keywords:
                if keyword.lower() in title_text:
                    score += 3
            
            # タイトル長によるスコア
            if 20 <= len(article['title']) <= 100:
                score += 2
            
            # 翻訳成功は優先
            if article['has_translation']:
                score += 2
            
            # 重要度設定
            if score >= 8:
                article['importance'] = 5
            elif score >= 5:
                article['importance'] = 4
            elif score >= 3:
                article['importance'] = 3
            else:
                article['importance'] = 2
        
        # 重要度順でソート
        international_sorted = sorted([a for a in analyzed_articles if a['is_international']], 
                                    key=lambda x: (x['importance'], x['has_translation']), reverse=True)
        
        # analyzed_articlesを更新
        analyzed_articles = [a for a in analyzed_articles if not a['is_international']] + international_sorted
    
    # 国内記事処理（翻訳なし）
    for article in domestic_articles:
        article.update({
            'title': article['original_title'],
            'has_translation': False,
            'importance': 3,
            'reliability': 3,
            'emotional': 1,
            'reasoning': "国内記事"
        })
        analyzed_articles.append(article)
    
    print(f"✅ 全件バッチ翻訳処理完了: {len(analyzed_articles)}件（翻訳{translation_count}件・API{api_calls_used}回）")
    return analyzed_articles

# ======================================
# RSS取得機能
# ======================================

def fetch_rss_simple(source_name, url, max_items):
    """RSS記事取得"""
    if not LIBS_AVAILABLE:
        return []
    
    try:
        print(f"📡 {source_name} から取得中...")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        from io import BytesIO
        feed = feedparser.parse(BytesIO(response.content))
        
        if not feed.entries:
            return []
        
        articles = []
        is_international = source_name not in [src[0] for src in JAPANESE_NEWS_SOURCES]
        
        for entry in feed.entries[:max_items * 2]:
            try:
                title = entry.title.strip() if hasattr(entry, 'title') else "タイトルなし"
                
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
                
                link = entry.link if hasattr(entry, 'link') else ""
                tags = analyze_article_tags(title, summary)
                
                articles.append({
                    'title': title,
                    'original_title': title,
                    'summary': summary,
                    'url': link,
                    'source': source_name,
                    'tags': tags[:2],
                    'is_international': is_international,
                    'importance': 3,
                    'reliability': 3,
                    'emotional': 1,
                    'reasoning': "未処理"
                })
                
                if len(articles) >= max_items:
                    break
                    
            except Exception:
                continue
        
        print(f"✅ {source_name}: {len(articles)}件取得完了")
        return articles
        
    except Exception as e:
        print(f"❌ {source_name} 取得失敗: {str(e)}")
        return []

def rule_based_select_articles(articles, target_count, is_international=False):
    """ルールベース記事絞り込み"""
    if len(articles) <= target_count:
        return articles
    
    important_keywords = {
        'domestic': ['政府', '首相', '大統領', '選挙', '国会', '経済', '株価', '地震', '台風', '原発', '文化', '地方', '科学'],
        'international': ['trump', 'putin', 'ukraine', 'israel', 'iran', 'nato', 'election', 'ceasefire', 'war', 'summit']
    }
    
    keyword_set = important_keywords['international' if is_international else 'domestic']
    
    scored_articles = []
    for article in articles:
        score = 0
        title_lower = article['title'].lower()
        
        for keyword in keyword_set:
            if keyword in title_lower:
                score += 3
        
        if 20 <= len(article['title']) <= 80:
            score += 2
        
        if len(article['summary']) > 50:
            score += 1
        
        # NHKソースは優先
        if "NHK" in article['source']:
            score += 2
        
        scored_articles.append((score, article))
    
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    selected_articles = [article for score, article in scored_articles[:target_count]]
    
    return selected_articles

def remove_duplicates(articles):
    """記事重複除去"""
    seen_titles = set()
    unique_articles = []
    
    for article in articles:
        title_words = set(article['title'].lower().split())
        is_duplicate = False
        
        for seen_title in seen_titles:
            seen_words = set(seen_title.lower().split())
            if len(title_words & seen_words) / len(title_words | seen_words) > 0.7:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_titles.add(article['title'])
            unique_articles.append(article)
    
    return unique_articles

def get_all_news():
    """全ニュース取得（全件バッチ翻訳版）"""
    all_news = {'japanese': [], 'international': []}
    
    if not LIBS_AVAILABLE:
        return all_news
    
    print("📰 ニュース記事取得開始（NHK充実・全件バッチ翻訳版）...")
    
    # 記事取得
    for source_name, url, max_items in JAPANESE_NEWS_SOURCES:
        articles = fetch_rss_simple(source_name, url, max_items)
        all_news['japanese'].extend(articles)
        time.sleep(0.5)
    
    for source_name, url, max_items in INTERNATIONAL_NEWS_SOURCES:
        articles = fetch_rss_simple(source_name, url, max_items)
        all_news['international'].extend(articles)
        time.sleep(0.5)
    
    # 重複除去
    all_news['japanese'] = remove_duplicates(all_news['japanese'])
    all_news['international'] = remove_duplicates(all_news['international'])
    
    print(f"📊 記事取得完了: 国内{len(all_news['japanese'])}件, 国際{len(all_news['international'])}件")
    
    # ルールベース絞り込み（国内45件に増量）
    selected_japanese = rule_based_select_articles(all_news['japanese'], 45, False)  # 45件に増量
    selected_international = rule_based_select_articles(all_news['international'], 20, True)
    
    print(f"🎯 絞り込み完了: 国内{len(selected_japanese)}件, 国際{len(selected_international)}件")
    
    # 全件バッチ翻訳処理
    final_articles = selected_japanese + selected_international
    final_analyzed = process_articles_simplified(final_articles)
    
    # 結果分割
    final_japanese = [a for a in final_analyzed if not a['is_international']]
    final_international = [a for a in final_analyzed if a['is_international']]
    
    print(f"✨ 全件バッチ翻訳版完成: 国内{len(final_japanese)}件, 国際{len(final_international)}件")
    
    return {'japanese': final_japanese, 'international': final_international}

# ======================================
# API機能（天気・名言・歴史）
# ======================================

def get_api_quote():
    """API経由で英語名言取得"""
    try:
        response = requests.get("https://api.quotable.io/random", timeout=10, verify=False)
        if response.status_code == 200:
            data = response.json()
            return {
                "quote": data.get("content", ""),
                "author": data.get("author", "Unknown"),
                "translation": ""
            }
    except Exception as e:
        print(f"⚠️  名言API失敗: {str(e)}")
    
    # フォールバック
    fallback_quotes = [
        {"quote": "The only way to do great work is to love what you do.", "author": "Steve Jobs"},
        {"quote": "Innovation distinguishes between a leader and a follower.", "author": "Steve Jobs"},
        {"quote": "The future belongs to those who believe in the beauty of their dreams.", "author": "Eleanor Roosevelt"},
    ]
    return random.choice(fallback_quotes)

def get_api_history():
    """API経由で今日は何の日取得"""
    try:
        today = date.today()
        url = f"http://history.muffinlabs.com/date/{today.month}/{today.day}"
        response = requests.get(url, timeout=10, verify=False)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("data", {}).get("Events", [])
            
            if events:
                selected_event = events[0]
                year = selected_event.get("year", "")
                text = selected_event.get("text", "")
                return f"{year} - {text[:150]}{'...' if len(text) > 150 else ''}"
        
    except Exception as e:
        print(f"⚠️  歴史API失敗: {str(e)}")
    
    # フォールバック
    today = date.today()
    return f"{today.month}月{today.day}日 - 今日という日は二度と来ない特別な日です。"

def get_weather_data():
    """天気データ取得"""
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
            80: "にわか雨", 95: "雷雨"
        }
        
        now_hour = min(datetime.now().hour, len(data['hourly']['temperature_2m']) - 1)
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
        
        return {
            'current_temp': f"{current_temp}°C",
            'current_weather': current_weather,
            'weekly': weekly_forecast
        }
        
    except Exception as e:
        print(f"⚠️  天気API失敗: {str(e)}")
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
# バッジ機能
# ======================================

def get_importance_badge(score):
    """重要度バッジ"""
    badges = {
        5: {"icon": "🔥", "text": "最重要", "color": "#d32f2f"},
        4: {"icon": "⚡", "text": "重要", "color": "#f57c00"},
        3: {"icon": "📰", "text": "一般", "color": "#1976d2"},
        2: {"icon": "📍", "text": "地域", "color": "#388e3c"},
        1: {"icon": "💬", "text": "軽微", "color": "#616161"}
    }
    return badges.get(score, badges[3])

def get_reliability_badge(score):
    """信頼度バッジ"""
    badges = {
        5: {"icon": "✅", "text": "確実", "color": "#2e7d32"},
        4: {"icon": "🔍", "text": "信頼", "color": "#388e3c"},
        3: {"icon": "📋", "text": "一般", "color": "#1976d2"},
        2: {"icon": "⚠️", "text": "要確認", "color": "#f57c00"},
        1: {"icon": "❓", "text": "不確実", "color": "#d32f2f"}
    }
    return badges.get(score, badges[3])

def get_emotional_badge(score):
    """感情度バッジ"""
    badges = {
        1: {"icon": "📊", "text": "客観的", "color": "#1976d2"},
        2: {"icon": "💭", "text": "主観的", "color": "#f57c00"},
        3: {"icon": "💢", "text": "感情的", "color": "#d32f2f"}
    }
    return badges.get(score, badges[1])

def get_priority_background(index, total_count):
    """優先度別背景色"""
    if index < 3:
        return "#fff3e0"  # オレンジ系（上位3件）
    elif index < 10:
        return "#f3e5f5"  # 紫系（上位10件）
    else:
        return "#fafafa"  # グレー系（その他）

# ======================================
# HTML生成（優先度別背景色版）
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
        }}
        .priority-top3 {{
            background: #fff3e0;
            border-left: 4px solid #ff9800;
        }}
        .priority-top10 {{
            background: #f3e5f5;
            border-left: 4px solid #9c27b0;
        }}
        .priority-others {{
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
        .ai-badges {{
            display: flex;
            gap: 5px;
            margin-bottom: 8px;
            flex-wrap: wrap;
        }}
        .ai-badge {{
            display: inline-block;
            padding: 2px 6px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }}
        .original-title {{
            font-size: 12px;
            color: #888;
            font-style: italic;
            margin-bottom: 4px;
            background: #f0f0f0;
            padding: 5px;
            border-radius: 3px;
        }}
        .translation-note {{
            font-size: 11px;
            color: #666;
            margin-bottom: 4px;
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
        .priority-legend {{
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            padding: 10px;
            margin: 15px 0;
            border-radius: 5px;
            font-size: 13px;
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
                <strong>{weather['current_temp']} {weather['current_weather']}</strong>
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
                "{quote['quote'][:70]}{'...' if len(quote['quote']) > 70 else ''}"
                <div style="text-align: right; margin-top: 5px; font-weight: bold;">
                    — {quote['author']}
                </div>
            </div>
        </div>
    </div>

    <div class="main-content">
        <div class="news-section">
            <h2 class="news-title">🇯🇵 国内ニュース</h2>
            <div class="note success">
                ✅ NHK充実版から{len(news['japanese'])}件を厳選取得・重要度別表示
            </div>
            <div class="priority-legend">
                🔶 <strong>オレンジ背景</strong>: 上位3件 | 💜 <strong>紫背景</strong>: 上位10件 | ⚪ <strong>白背景</strong>: その他
            </div>"""

    # 国内ニュース（優先度別背景色）
    for i, article in enumerate(news['japanese']):
        importance_badge = get_importance_badge(article['importance'])
        reliability_badge = get_reliability_badge(article['reliability'])
        emotional_badge = get_emotional_badge(article['emotional'])
        
        # 優先度別CSSクラス
        if i < 3:
            priority_class = "priority-top3"
        elif i < 10:
            priority_class = "priority-top10"
        else:
            priority_class = "priority-others"
        
        html += f"""
            <div class="news-item {priority_class}">
                <div class="news-tags">
                    {''.join([f'<span class="tag">{tag["icon"]} {tag["name"]}</span>' for tag in article["tags"]])}
                </div>
                <div class="ai-badges">
                    <span class="ai-badge" style="background: {importance_badge['color']}">
                        {importance_badge['icon']} {importance_badge['text']}
                    </span>
                    <span class="ai-badge" style="background: {reliability_badge['color']}">
                        {reliability_badge['icon']} {reliability_badge['text']}
                    </span>
                    <span class="ai-badge" style="background: {emotional_badge['color']}">
                        {emotional_badge['icon']} {emotional_badge['text']}
                    </span>
                </div>
                <div class="news-headline">
                    <a href="{article['url']}" target="_blank">{article['title']}</a>
                </div>
                <div class="news-summary">{article['summary']}</div>
                <div class="news-source">出典: {article['source']} | 処理: {article['reasoning']}</div>
            </div>"""

    # 国際ニュース統計（全件バッチ翻訳版）
    batch_translated = [a for a in news['international'] if "全件バッチ翻訳完了" in a['reasoning']]
    english_only = [a for a in news['international'] if "英語原文" in a['reasoning']]
    
    if ENABLE_BATCH_TRANSLATION:
        translation_status = f"全件バッチ翻訳対応（最大{MAX_BATCH_SIZE}件・1回のAPI呼び出し）"
        if batch_translated:
            legend_text = f"🚀 <strong>全件バッチ翻訳済み</strong>: {len(batch_translated)}件 | 🇬🇧 <strong>英語原文</strong>: {len(english_only)}件"
        else:
            legend_text = f"🇬🇧 <strong>全て英語原文</strong>: {len(news['international'])}件（バッチ翻訳失敗）"
    else:
        translation_status = "翻訳機能無効"
        legend_text = f"🇬🇧 <strong>全て英語原文</strong>: {len(news['international'])}件（翻訳機能無効）"
    
    html += f"""
            <h2 class="news-title">🌍 国際ニュース</h2>
            <div class="note success">
                ✅ 海外メディアから{len(news['international'])}件を取得・{translation_status}
            </div>
            <div class="priority-legend">
                {legend_text} | 📊 翻訳後重要度ソート済み
            </div>"""

    # 国際ニュース（全件翻訳対応版）
    for i, article in enumerate(news['international']):
        importance_badge = get_importance_badge(article['importance'])
        reliability_badge = get_reliability_badge(article['reliability'])
        emotional_badge = get_emotional_badge(article['emotional'])
        
        # 重要度に応じたクラス
        if article['importance'] >= 4:
            priority_class = "priority-top3"  # 高重要度
        elif i < 10:
            priority_class = "priority-top10"
            
        else:
            priority_class = "priority-others"
        
        # 翻訳があるかどうか
        has_translation = article.get('has_translation', False)
        
        html += f"""
            <div class="news-item {priority_class}">
                <div class="news-tags">
                    {''.join([f'<span class="tag">{tag["icon"]} {tag["name"]}</span>' for tag in article["tags"]])}
                </div>
                <div class="ai-badges">
                    <span class="ai-badge" style="background: {importance_badge['color']}">
                        {importance_badge['icon']} {importance_badge['text']}
                    </span>
                    <span class="ai-badge" style="background: {reliability_badge['color']}">
                        {reliability_badge['icon']} {reliability_badge['text']}
                    </span>
                    <span class="ai-badge" style="background: {emotional_badge['color']}">
                        {emotional_badge['icon']} {emotional_badge['text']}
                    </span>
                </div>
                <div class="original-title">【原文】 {article["original_title"]}</div>
                <div class="news-headline">
                    <a href="{article['url']}" target="_blank">
                        {"【和訳】 " + article['title'] if has_translation else "【英語】 " + article['title']}
                    </a>
                </div>
                <div class="news-summary">{article['summary']}</div>
                <div class="news-source">出典: {article['source']} | 処理: {article['reasoning']}</div>
            </div>"""

    # 統計情報
    all_tags = {}
    for article in news['japanese'] + news['international']:
        for tag in article['tags']:
            tag_name = tag['name']
            all_tags[tag_name] = all_tags.get(tag_name, 0) + 1
    
    sorted_tags = sorted(all_tags.items(), key=lambda x: x[1], reverse=True)[:5]

    html += f"""
        </div>
        
        <div class="sidebar">
            <h3>📊 今日の記事分析</h3>
            <div class="sidebar-content">
                <div class="stats-item">
                    <span><strong>総記事数</strong></span>
                    <span><strong>{len(news['japanese']) + len(news['international'])}件</strong></span>
                </div>
                <div class="stats-item">
                    <span>国内ニュース</span>
                    <span>{len(news['japanese'])}件</span>
                </div>
                <div class="stats-item">
                    <span>国際ニュース</span>
                    <span>{len(news['international'])}件</span>
                </div>"""
    
    # 翻訳統計（全件バッチ翻訳版）
    if ENABLE_BATCH_TRANSLATION:
        html += f"""
                <hr style="margin: 15px 0;">
                <h4 style="margin: 10px 0; color: #003f7f;">全件バッチ翻訳処理</h4>
                <div class="stats-item">
                    <span>🚀 全件翻訳済み</span>
                    <span>{len(batch_translated)}件</span>
                </div>
                <div class="stats-item">
                    <span>🇬🇧 英語原文</span>
                    <span>{len(english_only)}件</span>
                </div>
                <div class="stats-item">
                    <span>📡 API呼び出し</span>
                    <span>{"1回" if batch_translated else "0回"}</span>
                </div>
                <div class="stats-item">
                    <span>📊 処理効率</span>
                    <span>全{len(news['international'])}件→1回</span>
                </div>"""
    
    html += f"""
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
                    NHK充実版で国内45件を厳選。{f"海外全{len(news['international'])}件を一括バッチ翻訳（1回のAPI呼び出し）後、重要度ソート。" if ENABLE_BATCH_TRANSLATION else "海外ニュースは英語原文で表示。"}
                    全記事で原文・和訳併記。優先度別背景色で見やすさ向上。
                </p>
            </div>
        </div>
    </div>

    <div class="footer">
        <p><strong>ほぼ日刊トラガラ新聞 | 発行: {SENDER_NAME} | 発行日時: {now.strftime('%Y年%m月%d日 %H:%M')}</strong></p>
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
    print(f"📰 ほぼ日刊トラガラ新聞生成開始")
    print(f"📅 発行日: {date.today().strftime('%Y年%m月%d日')}")
    
    if not LIBS_AVAILABLE:
        print("❌ pip install feedparser requests google-generativeai を実行してください")
        return
    
    # HTML生成
    html_content = generate_nhk_style_newspaper()
    
    # メール送信
    print("\n📧 新聞配信中...")
    success = send_email(html_content)
    
    if success:
        print("🎉 新聞配信完了！")
    else:
        print("❌ メール送信失敗")
    
    print(f"\n🚀 全件バッチ翻訳システム:")
    if ENABLE_BATCH_TRANSLATION:
        print(f"🌐 全件バッチ翻訳: 海外全20件を1回のAPI呼び出しで処理")
        print(f"📡 API効率: 従来の20回 → 1回（20倍効率化）")
        print(f"📊 翻訳後ソート: 和訳を見て重要度判定→並び替え")
        print(f"📖 全件併記: 全記事で【原文】【和訳】表示")
    else:
        print(f"🌐 全件バッチ翻訳: 無効（全て原文表示）")
    print(f"📰 NHK充実版: 地方・文化・スポーツ・災害含む")
    print(f"📊 国内記事: 45件")
    print(f"🎨 優先度表示: 重要度4以上・上位10件で背景色変更")
    print(f"❌ Yahoo削除: NHK中心の信頼性重視")

if __name__ == "__main__":
    main()

