#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Your Private Memo - シンプルローカルwebサーバー版
sypm.py (Simple Your Private Memo)
"""

import http.server
import socketserver
import json
import urllib.parse
import datetime
import html
import os
import webbrowser
import threading
import time

class MemoHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/' or self.path == '/memo.html':
            self.serve_memo_page()
        elif self.path == '/bookmarklet.js':
            self.serve_bookmarklet()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/save':
            self.handle_save_memo()
        elif self.path == '/delete':
            self.handle_delete_memo()
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """CORS プリフライトリクエストを処理"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_memo_page(self):
        """メモ表示ページを配信"""
        memo_file = 'memo-data.json'
        memos = []
        
        if os.path.exists(memo_file):
            try:
                with open(memo_file, 'r', encoding='utf-8') as f:
                    memos = json.load(f)
            except:
                memos = []
        
        # HTML生成
        html_content = self.generate_memo_html(memos)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_bookmarklet(self):
        """ブックマークレットJavaScriptを配信"""
        bookmarklet_code = """
javascript:(function(){
    var selectedText = window.getSelection().toString();
    if (!selectedText) {
        alert('❌ テキストを選択してください');
        return;
    }
    
    var data = {
        text: selectedText,
        url: window.location.href,
        title: document.title
    };
    
    fetch('http://localhost:8000/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            alert('✅ SYPM 保存完了\\n' + selectedText.substring(0, 50) + '...');
        } else {
            alert('❌ 保存エラー');
        }
    })
    .catch(error => {
        alert('❌ サーバーに接続できません\\nまず sypm.py を実行してください');
    });
})();
        """.strip()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(bookmarklet_code.encode('utf-8'))
    
    def handle_save_memo(self):
        """メモ保存処理"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # 新しいメモエントリ
            memo_entry = {
                'id': int(time.time() * 1000),  # ユニークID
                'text': data['text'],
                'url': data['url'],
                'title': data['title'],
                'timestamp': datetime.datetime.now().isoformat(),
                'formatted_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 既存メモ読み込み
            memo_file = 'memo-data.json'
            memos = []
            if os.path.exists(memo_file):
                try:
                    with open(memo_file, 'r', encoding='utf-8') as f:
                        memos = json.load(f)
                except:
                    memos = []
            
            # 新しいメモを先頭に追加
            memos.insert(0, memo_entry)
            
            # ファイル保存
            with open(memo_file, 'w', encoding='utf-8') as f:
                json.dump(memos, f, ensure_ascii=False, indent=2)
            
            # レスポンス
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'status': 'success', 'message': '保存完了'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
            print(f"✅ メモ保存: {len(data['text'])}文字 - {data['title']}")
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
            self.send_error(500)
    
    def handle_delete_memo(self):
        """メモ削除処理"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            memo_id = int(data['memo_id'])
            
            # 既存メモ読み込み
            memo_file = 'memo-data.json'
            memos = []
            if os.path.exists(memo_file):
                try:
                    with open(memo_file, 'r', encoding='utf-8') as f:
                        memos = json.load(f)
                except:
                    memos = []
            
            # 指定IDのメモを削除
            original_count = len(memos)
            memos = [memo for memo in memos if memo['id'] != memo_id]
            deleted_count = original_count - len(memos)
            
            if deleted_count > 0:
                # ファイル更新
                with open(memo_file, 'w', encoding='utf-8') as f:
                    json.dump(memos, f, ensure_ascii=False, indent=2)
                
                print(f"🗑️ メモ削除完了: ID {memo_id}")
                
                # 成功レスポンス
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'status': 'success', 'message': '削除完了', 'deleted_count': deleted_count}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                # 該当メモが見つからない
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'status': 'error', 'message': 'メモが見つかりません'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ 削除エラー: {e}")
            self.send_error(500)
    
    def generate_memo_html(self, memos):
        """メモ表示HTML生成"""
        memo_items = ""
        for memo in memos:
            escaped_text = html.escape(memo['text'])
            escaped_url = html.escape(memo['url'])
            escaped_title = html.escape(memo['title'])
            
            memo_items += f"""
            <div class="memo-item" data-id="{memo['id']}">
                <div class="memo-header">
                    <span class="timestamp">📅 {memo['formatted_time']}</span>
                    <a href="{escaped_url}" target="_blank" class="source">🔗 {escaped_title}</a>
                </div>
                <div class="memo-content">{escaped_text}</div>
                <div class="memo-actions">
                    <button onclick="copyMemoWithUrl(this, '{memo['id']}')">📋 コピー（URL付）</button>
                    <button onclick="generatePrompts(this, '{memo['id']}')">🤖 AIプロンプト生成</button>
                    <button onclick="deleteMemo(this, '{memo['id']}')">🗑️ 削除</button>
                </div>
                <div class="prompt-section" id="prompts-{memo['id']}" style="display:none;">
                    <h4>🤖 生成済みプロンプト</h4>
                    <div class="prompt-grid">
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>📚 解説プロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下を解説してください：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🔍 事実確認プロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下の内容を事実確認してください：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>⚖️ 意見・事実分離プロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下の内容について、意見と事実を分けて整理してください：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🇯🇵 和訳プロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下を和訳してください：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🇺🇸 英訳プロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下を英訳してください：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🔄 多角的フィードバックプロンプト</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 コピー</button>
                            </div>
                            <textarea readonly>以下について、一般的な結論・意見・感想、賛成・反対・盲点・確率・統計・人文科学・社会科学・自然科学・私のメタ認知を支援する観点から、必要な観点を選び、多角的なフィードバックをお願いします：

{escaped_text}

出典: {escaped_url}</textarea>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🔒 Simple Your Private Memo</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            background: rgba(255,255,255,0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            text-align: center;
            backdrop-filter: blur(10px);
        }}
        .header h1 {{
            color: #333;
            margin-bottom: 10px;
        }}
        .stats {{
            background: rgba(255,255,255,0.9);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .bookmarklet-section {{
            background: rgba(255,255,255,0.95);
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .bookmarklet-code {{
            background: #f8f9fa;
            border: 2px dashed #667eea;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            margin: 10px 0;
        }}
        .bookmarklet-link {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px;
        }}
        .memo-item {{
            background: rgba(255,255,255,0.95);
            margin: 20px 0;
            padding: 20px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
            border-left: 4px solid #667eea;
        }}
        .memo-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
            font-size: 0.9em;
            color: #666;
        }}
        .memo-content {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin: 15px 0;
            white-space: pre-wrap;
            line-height: 1.6;
        }}
        .memo-actions {{
            margin-top: 15px;
        }}
        .memo-actions button {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
        }}
        .memo-actions button:hover {{
            background: #5a6fd8;
        }}
        .source {{
            color: #667eea;
            text-decoration: none;
        }}
        .source:hover {{
            text-decoration: underline;
        }}
        .empty-state {{
            text-align: center;
            padding: 50px;
            color: rgba(255,255,255,0.8);
        }}
        .prompt-section {{
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }}
        .prompt-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .prompt-item {{
            background: white;
            padding: 15px;
            border-radius: 5px;
            border-left: 3px solid #667eea;
        }}
        .prompt-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .prompt-item strong {{
            color: #333;
        }}
        .copy-prompt-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 11px;
        }}
        .copy-prompt-btn:hover {{
            background: #218838;
        }}
        .prompt-item textarea {{
            width: 100%;
            height: 120px;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 8px;
            font-size: 12px;
            resize: vertical;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Simple Your Private Memo</h1>
            <p>プライベート・メモ管理システム</p>
            <p><strong>100%ローカル保存 - データ主権保護</strong></p>
        </div>
        
        <div class="stats">
            <div>📝 保存済みメモ: {len(memos)}件</div>
            <div>🛡️ プライバシー: 完全保護</div>
            <div>🔄 自動更新</div>
        </div>
        
        <div class="bookmarklet-section">
            <h3>📌 メモ保存方法</h3>
            
            <div class="save-methods">
                <div class="method-card">
                    <h4>🚀 方法1: ブックマークレット（推奨）</h4>
                    <p>下記リンクをブックマークバーにドラッグ&ドロップ:</p>
                    <div class="bookmarklet-code">
                        <a href="javascript:(function(){{var selectedText = window.getSelection().toString();if (!selectedText) {{alert('❌ テキストを選択してください');return;}}var data = {{text: selectedText,url: window.location.href,title: document.title}};fetch('http://localhost:8000/save', {{method: 'POST',headers: {{'Content-Type': 'application/json'}},body: JSON.stringify(data)}}).then(response => response.json()).then(result => {{if (result.status === 'success') {{alert('✅ SYPM 保存完了\\n' + selectedText.substring(0, 50) + '...');}} else {{alert('❌ 保存エラー');}}}} ).catch(error => {{alert('❌ サーバーに接続できません\\nまず sypm.py を実行してください');}});}})();" class="bookmarklet-link">📌 SYPM</a>
                    </div>
                    <p><strong>使用方法:</strong> テキスト選択 → ブックマーク「SYPM」クリック</p>
                </div>
                
                <div class="method-card">
                    <h4>✋ 方法2: 手動保存（サイトにより機能しない場合の代替手段）</h4>
                    <p>ブックマークレットが動作しない場合は、この入力欄をご利用ください</p>
                    <form id="manual-save-form">
                        <div class="input-group">
                            <label for="manual-text">📝 メモ内容:</label>
                            <textarea id="manual-text" placeholder="保存したいテキストをここに貼り付け" rows="4"></textarea>
                        </div>
                        <div class="input-group">
                            <label for="manual-url">🔗 URL（任意）:</label>
                            <input type="text" id="manual-url" placeholder="https://example.com（空欄可）">
                        </div>
                        <div class="input-group">
                            <label for="manual-title">📄 タイトル（任意）:</label>
                            <input type="text" id="manual-title" placeholder="ページタイトル（空欄可）">
                        </div>
                        <button type="submit" class="manual-save-btn">💾 手動保存</button>
                    </form>
                </div>
            </div>
        </div>
        
        {memo_items if memos else '<div class="empty-state"><h2>📝 メモがまだありません</h2><p>ブックマークレットを設定して、最初のメモを保存してみましょう！</p></div>'}
    </div>
    
    <script>
        function copyMemoWithUrl(button, memoId) {{
            const memoItem = button.closest('.memo-item');
            const content = memoItem.querySelector('.memo-content').textContent;
            const sourceLink = memoItem.querySelector('.source').href;
            const sourceTitle = memoItem.querySelector('.source').textContent.replace('🔗 ', '');
            
            const fullText = `${{content}}

出典: ${{sourceTitle}}
URL: ${{sourceLink}}`;
            
            navigator.clipboard.writeText(fullText).then(() => {{
                button.textContent = '✅ コピー完了';
                setTimeout(() => {{ button.textContent = '📋 コピー（URL付）'; }}, 2000);
            }});
        }}
        
        function generatePrompts(button, memoId) {{
            const promptSection = document.getElementById(`prompts-${{memoId}}`);
            if (promptSection.style.display === 'none') {{
                promptSection.style.display = 'block';
                button.textContent = '🙈 プロンプト非表示';
            }} else {{
                promptSection.style.display = 'none';
                button.textContent = '🤖 AIプロンプト生成';
            }}
        }}
        
        function copySpecificPrompt(button) {{
            const promptItem = button.closest('.prompt-item');
            const textarea = promptItem.querySelector('textarea');
            
            navigator.clipboard.writeText(textarea.value).then(() => {{
                const originalText = button.textContent;
                button.textContent = '✅ コピー完了';
                button.style.backgroundColor = '#218838';
                
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.style.backgroundColor = '#28a745';
                }}, 2000);
            }}).catch(err => {{
                // フォールバック: テキスト選択
                textarea.select();
                document.execCommand('copy');
                button.textContent = '✅ コピー完了';
                setTimeout(() => {{
                    button.textContent = '📋 コピー';
                }}, 2000);
            }});
        }}
        
        function deleteMemo(button, memoId) {{
            if (confirm('このメモを削除しますか？\\n\\n削除したメモは復元できません。')) {{
                // 削除処理開始
                button.disabled = true;
                button.textContent = '🔄 削除中...';
                
                fetch('/delete', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{memo_id: parseInt(memoId)}})
                }})
                .then(response => response.json())
                .then(result => {{
                    if (result.status === 'success') {{
                        // 削除成功 - メモアイテムをフェードアウト
                        const memoItem = button.closest('.memo-item');
                        memoItem.style.transition = 'opacity 0.5s ease-out';
                        memoItem.style.opacity = '0';
                        
                        setTimeout(() => {{
                            memoItem.remove();
                            // メモ数更新
                            updateMemoCount();
                        }}, 500);
                        
                        console.log('✅ メモ削除完了');
                    }} else {{
                        alert('❌ 削除エラー: ' + result.message);
                        button.disabled = false;
                        button.textContent = '🗑️ 削除';
                    }}
                }})
                .catch(error => {{
                    alert('❌ 削除処理でエラーが発生しました');
                    button.disabled = false;
                    button.textContent = '🗑️ 削除';
                    console.error('削除エラー:', error);
                }});
            }}
        }}
        
        function updateMemoCount() {{
            const memoItems = document.querySelectorAll('.memo-item');
            const statsDiv = document.querySelector('.stats');
            if (statsDiv) {{
                const memoCount = memoItems.length;
                statsDiv.innerHTML = `
                    <div>📝 保存済みメモ: ${{memoCount}}件</div>
                    <div>🛡️ プライバシー: 完全保護</div>
                    <div>🔄 自動更新</div>
                `;
                
                // メモが0件になった場合の表示
                if (memoCount === 0) {{
                    const container = document.querySelector('.container');
                    const emptyState = document.createElement('div');
                    emptyState.className = 'empty-state';
                    emptyState.innerHTML = '<h2>📝 メモがまだありません</h2><p>ブックマークレットを設定して、最初のメモを保存してみましょう！</p>';
                    container.appendChild(emptyState);
                }}
            }}
        }}
        
        // 自動リロード（新しいメモ確認）
        setInterval(() => {{
            if (document.hidden) return;
            fetch('/memo.html').then(() => {{
                // 必要に応じてページ更新
            }});
        }}, 5000);
        
        // 手動保存フォーム処理
        document.getElementById('manual-save-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const textContent = document.getElementById('manual-text').value.trim();
            const urlContent = document.getElementById('manual-url').value.trim();
            const titleContent = document.getElementById('manual-title').value.trim();
            
            if (!textContent) {{
                alert('❌ メモ内容を入力してください');
                return;
            }}
            
            const submitButton = document.querySelector('.manual-save-btn');
            submitButton.disabled = true;
            submitButton.textContent = '💾 保存中...';
            
            const data = {{
                text: textContent,
                url: urlContent || '手動入力',
                title: titleContent || '手動保存メモ'
            }};
            
            fetch('/save', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.status === 'success') {{
                    alert('✅ 手動保存完了\\n' + textContent.substring(0, 50) + '...');
                    // フォームリセット
                    document.getElementById('manual-text').value = '';
                    document.getElementById('manual-url').value = '';
                    document.getElementById('manual-title').value = '';
                    // ページリロード（新しいメモを表示）
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 1000);
                }} else {{
                    alert('❌ 保存エラー');
                }}
            }})
            .catch(error => {{
                alert('❌ サーバーエラー\\nサーバーが起動しているか確認してください');
                console.error('手動保存エラー:', error);
            }})
            .finally(() => {{
                submitButton.disabled = false;
                submitButton.textContent = '💾 手動保存';
            }});
        }});
        
        // URLフィールドの自動入力（リファラー取得試行）
        window.addEventListener('load', function() {{
            const urlField = document.getElementById('manual-url');
            if (document.referrer && document.referrer !== window.location.href) {{
                urlField.placeholder = 'コピー元: ' + document.referrer;
            }}
        }});
    </script>
</body>
</html>"""


def open_browser():
    """ブラウザを自動で開く"""
    time.sleep(1)  # サーバー起動を待つ
    webbrowser.open('http://localhost:8000')


def main():
    """メイン処理"""
    print("🔒 Simple Your Private Memo")
    print("🚀 ローカルサーバー起動中...")
    
    # ブラウザを別スレッドで開く
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # サーバー起動
    PORT = 8000
    Handler = MemoHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ サーバー起動完了: http://localhost:{PORT}")
            print("🔗 ブラウザが自動で開きます")
            print("📌 ブックマークレットを設定してください")
            print("⚠️  終了するには Ctrl+C を押してください")
            print("")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 SYPM サーバー停止")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ ポート{PORT}は既に使用されています")
            print("他のSYPMが起動中の可能性があります")
        else:
            print(f"❌ サーバー起動エラー: {e}")


if __name__ == "__main__":
    main()
