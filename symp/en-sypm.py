#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple Your Private Memo - English Version
sypm-en.py (Simple Your Private Memo - English)
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
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def serve_memo_page(self):
        """Serve memo display page"""
        memo_file = 'memo-data-en.json'
        memos = []
        
        if os.path.exists(memo_file):
            try:
                with open(memo_file, 'r', encoding='utf-8') as f:
                    memos = json.load(f)
            except:
                memos = []
        
        # Generate HTML
        html_content = self.generate_memo_html(memos)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_bookmarklet(self):
        """Serve bookmarklet JavaScript"""
        bookmarklet_code = """
javascript:(function(){
    var selectedText = window.getSelection().toString();
    if (!selectedText) {
        alert('❌ Please select text first');
        return;
    }
    
    var data = {
        text: selectedText,
        url: window.location.href,
        title: document.title
    };
    
    fetch('http://localhost:8001/save', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.status === 'success') {
            alert('✅ SYPM saved successfully\\n' + selectedText.substring(0, 50) + '...');
        } else {
            alert('❌ Save error');
        }
    })
    .catch(error => {
        alert('❌ Cannot connect to server\\nPlease run sypm-en.py first');
    });
})();
        """.strip()
        
        self.send_response(200)
        self.send_header('Content-type', 'application/javascript')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(bookmarklet_code.encode('utf-8'))
    
    def handle_save_memo(self):
        """Handle memo save"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            
            # New memo entry
            memo_entry = {
                'id': int(time.time() * 1000),  # Unique ID
                'text': data['text'],
                'url': data['url'],
                'title': data['title'],
                'timestamp': datetime.datetime.now().isoformat(),
                'formatted_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Load existing memos
            memo_file = 'memo-data-en.json'
            memos = []
            if os.path.exists(memo_file):
                try:
                    with open(memo_file, 'r', encoding='utf-8') as f:
                        memos = json.load(f)
                except:
                    memos = []
            
            # Add new memo to beginning
            memos.insert(0, memo_entry)
            
            # Save file
            with open(memo_file, 'w', encoding='utf-8') as f:
                json.dump(memos, f, ensure_ascii=False, indent=2)
            
            # Response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {'status': 'success', 'message': 'Saved successfully'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
            print(f"✅ Memo saved: {len(data['text'])} chars - {data['title']}")
            
        except Exception as e:
            print(f"❌ Save error: {e}")
            self.send_error(500)
    
    def handle_delete_memo(self):
        """Handle memo deletion"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            memo_id = int(data['memo_id'])
            
            # Load existing memos
            memo_file = 'memo-data-en.json'
            memos = []
            if os.path.exists(memo_file):
                try:
                    with open(memo_file, 'r', encoding='utf-8') as f:
                        memos = json.load(f)
                except:
                    memos = []
            
            # Delete memo with specified ID
            original_count = len(memos)
            memos = [memo for memo in memos if memo['id'] != memo_id]
            deleted_count = original_count - len(memos)
            
            if deleted_count > 0:
                # Update file
                with open(memo_file, 'w', encoding='utf-8') as f:
                    json.dump(memos, f, ensure_ascii=False, indent=2)
                
                print(f"🗑️ Memo deleted: ID {memo_id}")
                
                # Success response
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'status': 'success', 'message': 'Deleted successfully', 'deleted_count': deleted_count}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            else:
                # Memo not found
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                response = {'status': 'error', 'message': 'Memo not found'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
                
        except Exception as e:
            print(f"❌ Delete error: {e}")
            self.send_error(500)
    
    def generate_memo_html(self, memos):
        """Generate memo display HTML"""
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
                    <button onclick="copyMemoWithUrl(this, '{memo['id']}')">📋 Copy (with URL)</button>
                    <button onclick="generatePrompts(this, '{memo['id']}')">🤖 Generate AI Prompts</button>
                    <button onclick="deleteMemo(this, '{memo['id']}')">🗑️ Delete</button>
                </div>
                <div class="prompt-section" id="prompts-{memo['id']}" style="display:none;">
                    <h4>🤖 Generated Prompts</h4>
                    <div class="prompt-grid">
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>📚 Explanation Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please explain the following:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🔍 Fact-check Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please fact-check the following content:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>⚖️ Opinion-Fact Separation Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please separate opinions and facts in the following content:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🇯🇵 Japanese Translation Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please translate the following to Japanese:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🇺🇸 English Translation Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please translate the following to English:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                        <div class="prompt-item">
                            <div class="prompt-header">
                                <strong>🔄 Multi-perspective Analysis Prompt</strong>
                                <button class="copy-prompt-btn" onclick="copySpecificPrompt(this)">📋 Copy</button>
                            </div>
                            <textarea readonly>Please provide multi-perspective feedback on the following from various angles (general conclusions, pros/cons, blind spots, statistics, humanities, social sciences, natural sciences, metacognitive support) as needed:

{escaped_text}

Source: {escaped_url}</textarea>
                        </div>
                    </div>
                </div>
            </div>
            """
        
        return f"""<!DOCTYPE html>
<html lang="en">
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
        .save-methods {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 15px;
        }}
        .method-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .method-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .input-group {{
            margin-bottom: 15px;
        }}
        .input-group label {{
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
            color: #555;
        }}
        .input-group textarea, .input-group input {{
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }}
        .input-group textarea {{
            resize: vertical;
            min-height: 80px;
        }}
        .manual-save-btn {{
            background: #28a745;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            width: 100%;
        }}
        .manual-save-btn:hover {{
            background: #218838;
        }}
        .manual-save-btn:disabled {{
            background: #6c757d;
            cursor: not-allowed;
        }}
        @media (max-width: 768px) {{
            .save-methods {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 Simple Your Private Memo</h1>
            <p>Private Memo Management System</p>
            <p><strong>100% Local Storage - Data Sovereignty Protection</strong></p>
        </div>
        
        <div class="stats">
            <div>📝 Saved Memos: {len(memos)} items</div>
            <div>🛡️ Privacy: Fully Protected</div>
            <div>🔄 Auto Update</div>
        </div>
        
        <div class="bookmarklet-section">
            <h3>📌 Memo Save Methods</h3>
            
            <div class="save-methods">
                <div class="method-card">
                    <h4>🚀 Method 1: Bookmarklet (Recommended)</h4>
                    <p>Drag and drop the link below to your bookmark bar:</p>
                    <div class="bookmarklet-code">
                        <a href="javascript:(function(){{var selectedText = window.getSelection().toString();if (!selectedText) {{alert('❌ Please select text first');return;}}var data = {{text: selectedText,url: window.location.href,title: document.title}};fetch('http://localhost:8001/save', {{method: 'POST',headers: {{'Content-Type': 'application/json'}},body: JSON.stringify(data)}}).then(response => response.json()).then(result => {{if (result.status === 'success') {{alert('✅ SYPM saved successfully\\n' + selectedText.substring(0, 50) + '...');}} else {{alert('❌ Save error');}}}} ).catch(error => {{alert('❌ Cannot connect to server\\nPlease run sypm-en.py first');}});}})();" class="bookmarklet-link">📌 SYPM</a>
                    </div>
                    <p><strong>Usage:</strong> Select text → Click bookmark "SYPM"</p>
                </div>
                
                <div class="method-card">
                    <h4>✋ Method 2: Manual Save (Alternative Method)</h4>
                    <p>If the bookmarklet doesn't work on some sites, please use this input form</p>
                    <form id="manual-save-form">
                        <div class="input-group">
                            <label for="manual-text">📝 Memo Content:</label>
                            <textarea id="manual-text" placeholder="Paste the text you want to save here" rows="4"></textarea>
                        </div>
                        <div class="input-group">
                            <label for="manual-url">🔗 URL (Optional):</label>
                            <input type="text" id="manual-url" placeholder="https://example.com (can be empty)">
                        </div>
                        <div class="input-group">
                            <label for="manual-title">📄 Title (Optional):</label>
                            <input type="text" id="manual-title" placeholder="Page title (can be empty)">
                        </div>
                        <button type="submit" class="manual-save-btn">💾 Manual Save</button>
                    </form>
                </div>
            </div>
        </div>
        
        {memo_items if memos else '<div class="empty-state"><h2>📝 No memos yet</h2><p>Set up the bookmarklet and save your first memo!</p></div>'}
    </div>
    
    <script>
        function copyMemoWithUrl(button, memoId) {{
            const memoItem = button.closest('.memo-item');
            const content = memoItem.querySelector('.memo-content').textContent;
            const sourceLink = memoItem.querySelector('.source').href;
            const sourceTitle = memoItem.querySelector('.source').textContent.replace('🔗 ', '');
            
            const fullText = `${{content}}

Source: ${{sourceTitle}}
URL: ${{sourceLink}}`;
            
            navigator.clipboard.writeText(fullText).then(() => {{
                button.textContent = '✅ Copied';
                setTimeout(() => {{ button.textContent = '📋 Copy (with URL)'; }}, 2000);
            }});
        }}
        
        function generatePrompts(button, memoId) {{
            const promptSection = document.getElementById(`prompts-${{memoId}}`);
            if (promptSection.style.display === 'none') {{
                promptSection.style.display = 'block';
                button.textContent = '🙈 Hide Prompts';
            }} else {{
                promptSection.style.display = 'none';
                button.textContent = '🤖 Generate AI Prompts';
            }}
        }}
        
        function copySpecificPrompt(button) {{
            const promptItem = button.closest('.prompt-item');
            const textarea = promptItem.querySelector('textarea');
            
            navigator.clipboard.writeText(textarea.value).then(() => {{
                const originalText = button.textContent;
                button.textContent = '✅ Copied';
                button.style.backgroundColor = '#218838';
                
                setTimeout(() => {{
                    button.textContent = originalText;
                    button.style.backgroundColor = '#28a745';
                }}, 2000);
            }}).catch(err => {{
                textarea.select();
                document.execCommand('copy');
                button.textContent = '✅ Copied';
                setTimeout(() => {{
                    button.textContent = '📋 Copy';
                }}, 2000);
            }});
        }}
        
        function deleteMemo(button, memoId) {{
            if (confirm('Delete this memo?\\n\\nDeleted memos cannot be restored.')) {{
                button.disabled = true;
                button.textContent = '🔄 Deleting...';
                
                fetch('/delete', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{memo_id: parseInt(memoId)}})
                }})
                .then(response => response.json())
                .then(result => {{
                    if (result.status === 'success') {{
                        const memoItem = button.closest('.memo-item');
                        memoItem.style.transition = 'opacity 0.5s ease-out';
                        memoItem.style.opacity = '0';
                        
                        setTimeout(() => {{
                            memoItem.remove();
                            updateMemoCount();
                        }}, 500);
                        
                        console.log('✅ Memo deleted');
                    }} else {{
                        alert('❌ Delete error: ' + result.message);
                        button.disabled = false;
                        button.textContent = '🗑️ Delete';
                    }}
                }})
                .catch(error => {{
                    alert('❌ Error occurred during deletion');
                    button.disabled = false;
                    button.textContent = '🗑️ Delete';
                    console.error('Delete error:', error);
                }});
            }}
        }}
        
        function updateMemoCount() {{
            const memoItems = document.querySelectorAll('.memo-item');
            const statsDiv = document.querySelector('.stats');
            if (statsDiv) {{
                const memoCount = memoItems.length;
                statsDiv.innerHTML = `
                    <div>📝 Saved Memos: ${{memoCount}} items</div>
                    <div>🛡️ Privacy: Fully Protected</div>
                    <div>🔄 Auto Update</div>
                `;
                
                if (memoCount === 0) {{
                    const container = document.querySelector('.container');
                    const emptyState = document.createElement('div');
                    emptyState.className = 'empty-state';
                    emptyState.innerHTML = '<h2>📝 No memos yet</h2><p>Set up the bookmarklet and save your first memo!</p>';
                    container.appendChild(emptyState);
                }}
            }}
        }}
        
        // Auto-reload
        setInterval(() => {{
            if (document.hidden) return;
            fetch('/memo.html').then(() => {{
                // Refresh if needed
            }});
        }}, 5000);
        
        // Manual save form
        document.getElementById('manual-save-form').addEventListener('submit', function(e) {{
            e.preventDefault();
            
            const textContent = document.getElementById('manual-text').value.trim();
            const urlContent = document.getElementById('manual-url').value.trim();
            const titleContent = document.getElementById('manual-title').value.trim();
            
            if (!textContent) {{
                alert('❌ Please enter memo content');
                return;
            }}
            
            const submitButton = document.querySelector('.manual-save-btn');
            submitButton.disabled = true;
            submitButton.textContent = '💾 Saving...';
            
            const data = {{
                text: textContent,
                url: urlContent || 'Manual input',
                title: titleContent || 'Manual saved memo'
            }};
            
            fetch('/save', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify(data)
            }})
            .then(response => response.json())
            .then(result => {{
                if (result.status === 'success') {{
                    alert('✅ Manual save completed\\n' + textContent.substring(0, 50) + '...');
                    document.getElementById('manual-text').value = '';
                    document.getElementById('manual-url').value = '';
                    document.getElementById('manual-title').value = '';
                    setTimeout(() => {{
                        window.location.reload();
                    }}, 1000);
                }} else {{
                    alert('❌ Save error');
                }}
            }})
            .catch(error => {{
                alert('❌ Server error\\nPlease check if the server is running');
                console.error('Manual save error:', error);
            }})
            .finally(() => {{
                submitButton.disabled = false;
                submitButton.textContent = '💾 Manual Save';
            }});
        }});
        
        // Auto-fill URL field
        window.addEventListener('load', function() {{
            const urlField = document.getElementById('manual-url');
            if (document.referrer && document.referrer !== window.location.href) {{
                urlField.placeholder = 'Copy source: ' + document.referrer;
            }}
        }});
    </script>
</body>
</html>"""


def open_browser():
    """Auto-open browser"""
    time.sleep(1)  # Wait for server startup
    webbrowser.open('http://localhost:8001')


def main():
    """Main process"""
    print("🔒 Simple Your Private Memo (English Version)")
    print("🚀 Starting local server...")
    
    # Open browser in separate thread
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start server
    PORT = 8001  # Different port from Japanese version
    Handler = MemoHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"✅ Server started: http://localhost:{PORT}")
            print("🔗 Browser will open automatically")
            print("📌 Please set up the bookmarklet")
            print("⚠️  Press Ctrl+C to stop")
            print("")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 SYPM server stopped")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use")
            print("Another SYPM may be running")
        else:
            print(f"❌ Server startup error: {e}")


if __name__ == "__main__":
    main()
