import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# Lưu trữ dữ liệu dạng: { "IP_Dien_Thoai": ["Nội dung 3", "Nội dung 2", "Nội dung 1"] }
clipboard_data = {}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trạm Copy Dữ Liệu</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 950px; margin: 20px auto; padding: 15px; background-color: #f4f6f9; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 20px; }
        textarea { width: 100%; height: 80px; padding: 10px; font-size: 15px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; }
        
        button { padding: 8px 15px; font-size: 14px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: bold; }
        button:hover { opacity: 0.9; }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .btn-refresh { background: #17a2b8; }
        
        .btn-row1 { background: #ffc107; color: #212529; }
        .btn-row2 { background: #fd7e14; color: white; }
        .btn-row3 { background: #20c997; color: white; }
        
        .btn-copy { background: #17a2b8; padding: 4px 10px; font-size: 12px; }
        .btn-copy-all { background: #6c757d; font-size: 12px; float: right; padding: 4px 10px; }
        
        .toolbar { display: flex; gap: 10px; margin-bottom: 15px; flex-wrap: wrap; align-items: center; }
        .toolbar-title { width: 100%; font-weight: bold; color: #495057; font-size: 14px; margin-bottom: 2px; margin-top: 5px; }
        
        .device-box { border: 1px solid #dcdcdc; margin-top: 15px; border-radius: 6px; background: #fff; overflow: hidden; }
        .ip-header { background: #e9ecef; padding: 8px 12px; font-weight: bold; color: #333; border-bottom: 1px solid #ddd; }
        
        .data-table { width: 100%; border-collapse: collapse; }
        .data-table tr { border-bottom: 1px solid #eee; }
        .data-table tr:last-child { border-bottom: none; }
        .data-table tr:hover { background-color: #f8f9fa; }
        .data-table td { padding: 8px 12px; font-size: 14px; vertical-align: middle; }
        
        .row-index { width: 60px; font-weight: bold; color: #6c757d; text-align: center; }
        .text-cell { font-family: Consolas, monospace; font-size: 15px; color: #111; word-break: break-all; }
        .action-cell { width: 90px; text-align: right; white-space: nowrap; }
    </style>
</head>
<body>
    <div class="card">
        <h2>📱 Gửi dữ liệu (Dành cho Điện thoại)</h2>
        <textarea id="content" placeholder="Dán nội dung cần gửi vào đây..."></textarea><br><br>
        <button onclick="sendData()" class="btn-success">Gửi lên Máy tính</button>
        <span id="send-status" style="margin-left: 10px; font-weight: bold; color: #28a745;"></span>
    </div>

    <div class="card">
        <h2>💻 Dữ liệu đã nhận (Dành cho Máy tính)</h2>
        
        <!-- Thanh công cụ Thao tác & Copy -->
        <div class="toolbar">
            <div class="toolbar-title">⚙️ Quản lý dữ liệu:</div>
            <button onclick="loadData()" class="btn-refresh">🔄 Làm mới ngay</button>
            <button onclick="clearAllData()" class="btn-danger">🗑️ Xóa sạch tất cả dữ liệu</button>

            <div class="toolbar-title">⚡ Copy hàng loạt tất cả IP:</div>
            <button onclick="copyRowAllIp(0)" class="btn-row1">📋 Copy DÒNG 1 (Mới nhất)</button>
            <button onclick="copyRowAllIp(1)" class="btn-row2">📋 Copy DÒNG 2</button>
            <button onclick="copyRowAllIp(2)" class="btn-row3">📋 Copy DÒNG 3</button>
        </div>

        <div id="pc-view">Đang chờ dữ liệu...</div>
    </div>

    <script>
        const HEADERS = { 'ngrok-skip-browser-warning': 'true' };

        function copyToClipboard(text) {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            } else {
                let textArea = document.createElement("textarea");
                textArea.value = text;
                textArea.style.position = "fixed";
                textArea.style.left = "-999999px";
                textArea.style.top = "-999999px";
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                return new Promise((resolve, reject) => {
                    document.execCommand('copy') ? resolve() : reject();
                    textArea.remove();
                });
            }
        }

        // Copy dòng chỉ định của TẤT CẢ IP
        function copyRowAllIp(rowIndex) {
            fetch('/api/data', { headers: HEADERS })
                .then(res => res.json())
                .then(data => {
                    const ips = Object.keys(data);
                    if (ips.length === 0) return alert('Chưa có dữ liệu nào!');

                    let rowItems = [];
                    for (let ip in data) {
                        if (data[ip] && data[ip].length > rowIndex) {
                            rowItems.push(data[ip][rowIndex]);
                        }
                    }

                    if (rowItems.length === 0) {
                        return alert('Không tìm thấy dữ liệu ở Dòng ' + (rowIndex + 1) + '!');
                    }

                    const combinedText = rowItems.join('\\n');
                    copyToClipboard(combinedText).then(() => {
                        alert('Đã copy Dòng ' + (rowIndex + 1) + ' của ' + rowItems.length + ' IP!');
                    }).catch(() => {
                        alert('Sao chép thất bại!');
                    });
                });
        }

        // Xóa toàn bộ dữ liệu trên server
        function clearAllData() {
            if (confirm('Bạn có chắc chắn muốn XÓA TẤT CẢ dữ liệu hiện tại không?')) {
                fetch('/api/clear', { method: 'POST', headers: HEADERS })
                    .then(res => res.json())
                    .then(data => {
                        if (data.status === 'ok') {
                            loadData();
                        }
                    });
            }
        }

        // Copy lẻ 1 dòng
        function copyText(text, btn) {
            copyToClipboard(text).then(() => {
                const originalText = btn.innerText;
                btn.innerText = '✓ Đã copy';
                btn.style.background = '#28a745';
                setTimeout(() => {
                    btn.innerText = originalText;
                    btn.style.background = '#17a2b8';
                }, 1200);
            });
        }

        // Copy tất cả của 1 IP
        function copyAllIp(ip) {
            fetch('/api/data', { headers: HEADERS })
                .then(res => res.json())
                .then(data => {
                    if (data[ip]) {
                        const allText = data[ip].join('\\n');
                        copyToClipboard(allText).then(() => {
                            alert('Đã copy toàn bộ nội dung của IP: ' + ip);
                        });
                    }
                });
        }

        // Gửi dữ liệu từ điện thoại
        function sendData() {
            const text = document.getElementById('content').value.trim();
            if (!text) return alert('Vui lòng nhập nội dung!');

            fetch('/send', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: 'content=' + encodeURIComponent(text)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    document.getElementById('content').value = '';
                    const status = document.getElementById('send-status');
                    status.innerText = '✅ Đã gửi!';
                    setTimeout(() => status.innerText = '', 2000);
                    loadData();
                }
            });
        }

        // Tải danh sách dữ liệu
        function loadData() {
            fetch('/api/data', { headers: HEADERS })
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('pc-view');
                    if (Object.keys(data).length === 0) {
                        container.innerHTML = '<p style="color: #777;">Chưa có dữ liệu nào được gửi lên.</p>';
                        return;
                    }

                    let html = '';
                    for (let ip in data) {
                        html += `<div class="device-box">
                            <div class="ip-header">
                                🔴 IP: ${ip}
                                <button class="btn-copy-all" onclick="copyAllIp('${ip}')">📋 Copy tất cả IP này</button>
                            </div>
                            <table class="data-table">`;
                        
                        data[ip].forEach((item, index) => {
                            const escapedItem = encodeURIComponent(item);
                            html += `<tr>
                                <td class="row-index">Dòng ${index + 1}</td>
                                <td class="text-cell">${item}</td>
                                <td class="action-cell">
                                    <button class="btn-copy" onclick="copyText(decodeURIComponent('${escapedItem}'), this)">Copy</button>
                                </td>
                            </tr>`;
                        });

                        html += `</table></div>`;
                    }
                    container.innerHTML = html;
                });
        }

        setInterval(loadData, 2000);
        loadData();
    </script>
</body>
</html>
"""

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/send', methods=['POST'])
def send_data():
    ip = get_client_ip()
    content = request.form.get('content')
    if content and content.strip():
        if ip not in clipboard_data:
            clipboard_data[ip] = []
        clipboard_data[ip].insert(0, content.strip())
    return jsonify({'status': 'ok'})

@app.route('/api/data')
def get_data():
    return jsonify(clipboard_data)

@app.route('/api/clear', methods=['POST'])
def clear_data():
    clipboard_data.clear()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
