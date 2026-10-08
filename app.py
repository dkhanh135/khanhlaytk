import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# Lưu trữ dữ liệu phân loại theo Mã cá nhân
clipboard_data = {}

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trạm Copy Dữ Liệu</title>
    <style>
        body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            max-width: 950px; 
            margin: 20px auto; 
            padding: 15px; 
            background-color: #f4f6f9; 
            position: relative;
        }
        
        /* Ô nhập Mã số cá nhân ở góc trên bên phải */
        .user-code-badge {
            position: absolute;
            top: 15px;
            right: 15px;
            background: #ffffff;
            border: 2px solid #007bff;
            padding: 6px 12px;
            border-radius: 20px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            gap: 6px;
            z-index: 1000;
        }
        .user-code-badge label {
            font-size: 13px;
            font-weight: bold;
            color: #007bff;
            white-space: nowrap;
        }
        .user-code-badge input {
            width: 110px;
            padding: 4px 8px;
            font-size: 14px;
            border: 1px solid #ccc;
            border-radius: 12px;
            outline: none;
            text-align: center;
            font-weight: bold;
            color: #dc3545;
        }
        .user-code-badge input:focus {
            border-color: #007bff;
        }

        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 20px; margin-top: 15px; }
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

        @media (max-width: 600px) {
            .user-code-badge { position: relative; top: 0; right: 0; margin-bottom: 10px; justify-content: center; }
            .card { margin-top: 0; }
        }
    </style>
</head>
<body>

    <!-- Ô NHẬP MÃ CÁ NHÂN GÓC TRÊN BÊN PHẢI -->
    <div class="user-code-badge">
        <label for="user-code">🔑 Mã cá nhân (*):</label>
        <input type="text" id="user-code" placeholder="Bắt buộc..." oninput="saveUserCode()">
    </div>

    <div class="card">
        <h2>📱 Gửi dữ liệu (Dành cho Điện thoại)</h2>
        <textarea id="content" placeholder="Dán nội dung cần gửi vào đây..."></textarea><br><br>
        <button onclick="sendData()" class="btn-success">Gửi lên Máy tính</button>
        <span id="send-status" style="margin-left: 10px; font-weight: bold;"></span>
    </div>

    <div class="card">
        <h2>💻 Dữ liệu đã nhận (Dành cho Máy tính)</h2>
        
        <!-- Thanh công cụ Thao tác & Copy -->
        <div class="toolbar">
            <div class="toolbar-title">⚙️ Quản lý dữ liệu:</div>
            <button onclick="loadData()" class="btn-refresh">🔄 Làm mới ngay</button>
            <button onclick="clearAllData()" class="btn-danger">🗑️ Xóa dữ liệu của mã này</button>

            <div class="toolbar-title">⚡ Copy hàng loạt:</div>
            <button onclick="copyRowAllIp(0)" class="btn-row1">📋 Copy DÒNG 1 (Mới nhất)</button>
            <button onclick="copyRowAllIp(1)" class="btn-row2">📋 Copy DÒNG 2</button>
            <button onclick="copyRowAllIp(2)" class="btn-row3">📋 Copy DÒNG 3</button>
        </div>

        <div id="pc-view">Đang kiểm tra Mã cá nhân...</div>
    </div>

    <script>
        const HEADERS = { 'ngrok-skip-browser-warning': 'true' };

        // Tự động khôi phục Mã số cá nhân từ bộ nhớ trình duyệt
        window.addEventListener('DOMContentLoaded', () => {
            const savedCode = localStorage.getItem('my_user_code');
            if (savedCode) {
                document.getElementById('user-code').value = savedCode;
            }
            loadData();
        });

        // Lưu mã cá nhân và làm mới giao diện
        function saveUserCode() {
            const code = document.getElementById('user-code').value.trim();
            localStorage.setItem('my_user_code', code);
            loadData();
        }

        function getUserCode() {
            return document.getElementById('user-code').value.trim();
        }

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

        // Copy dòng chỉ định thuộc Mã cá nhân hiện tại
        function copyRowAllIp(rowIndex) {
            const userCode = getUserCode();
            if (!userCode) {
                alert('⚠️ Bạn phải nhập Mã cá nhân ở góc trên bên phải trước!');
                document.getElementById('user-code').focus();
                return;
            }

            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status !== 'ok') return alert(res.message);
                    const data = res.data;
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
                        alert('Đã copy Dòng ' + (rowIndex + 1) + ' của ' + rowItems.length + ' mục!');
                    }).catch(() => {
                        alert('Sao chép thất bại!');
                    });
                });
        }

        // Xóa toàn bộ dữ liệu thuộc Mã cá nhân này
        function clearAllData() {
            const userCode = getUserCode();
            if (!userCode) {
                alert('⚠️ Bạn phải nhập Mã cá nhân ở góc trên bên phải!');
                document.getElementById('user-code').focus();
                return;
            }

            if (confirm('Bạn có chắc muốn XÓA TẤT CẢ dữ liệu của Mã "' + userCode + '" không?')) {
                fetch('/api/clear', { 
                    method: 'POST', 
                    headers: { 
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'ngrok-skip-browser-warning': 'true'
                    },
                    body: 'user_code=' + encodeURIComponent(userCode)
                })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'ok') {
                        loadData();
                    } else {
                        alert(data.message);
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

        // Copy tất cả nội dung của 1 thiết bị
        function copyAllIp(key) {
            const userCode = getUserCode();
            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status === 'ok' && res.data[key]) {
                        const allText = res.data[key].join('\\n');
                        copyToClipboard(allText).then(() => {
                            alert('Đã copy toàn bộ nội dung!');
                        });
                    }
                });
        }

        // GỬI DỮ LIỆU: BẮT BUỘC PHẢI CÓ MÃ
        function sendData() {
            const text = document.getElementById('content').value.trim();
            const userCode = getUserCode();

            if (!userCode) {
                alert('⚠️ BẮT BUỘC: Bạn phải nhập Mã cá nhân ở góc trên bên phải trước khi gửi!');
                document.getElementById('user-code').focus();
                return;
            }

            if (!text) {
                alert('Vui lòng nhập nội dung cần gửi!');
                return;
            }

            fetch('/send', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'ngrok-skip-browser-warning': 'true'
                },
                body: 'content=' + encodeURIComponent(text) + '&user_code=' + encodeURIComponent(userCode)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    document.getElementById('content').value = '';
                    const status = document.getElementById('send-status');
                    status.style.color = '#28a745';
                    status.innerText = '✅ Đã gửi thành công!';
                    setTimeout(() => status.innerText = '', 2000);
                    loadData();
                } else {
                    alert('❌ Lỗi: ' + data.message);
                }
            });
        }

        // LẤY DỮ LIỆU: BẮT BUỘC PHẢI CÓ MÃ
        function loadData() {
            const container = document.getElementById('pc-view');
            const userCode = getUserCode();

            if (!userCode) {
                container.innerHTML = '<p style="color: #dc3545; font-weight: bold; text-align: center; padding: 20px; background: #fff3f3; border: 1px solid #f5c6cb; border-radius: 6px;">⚠️ BẮT BUỘC NHẬP MÃ CÁ NHÂN Ở GÓC TRÊN BÊN PHẢI ĐỂ XEM / LẤY DỮ LIỆU!</p>';
                return;
            }

            fetch('/api/data?user_code=' + encodeURIComponent(userCode), { headers: HEADERS })
                .then(res => res.json())
                .then(res => {
                    if (res.status !== 'ok') {
                        container.innerHTML = `<p style="color: #dc3545;">⚠️ ${res.message}</p>`;
                        return;
                    }

                    const data = res.data;
                    if (Object.keys(data).length === 0) {
                        container.innerHTML = `<p style="color: #777;">Chưa có dữ liệu nào thuộc Mã cá nhân <b>"${userCode}"</b>.</p>`;
                        return;
                    }

                    let html = '';
                    for (let deviceKey in data) {
                        html += `<div class="device-box">
                            <div class="ip-header">
                                🔴 ${deviceKey}
                                <button class="btn-copy-all" onclick="copyAllIp('${deviceKey}')">📋 Copy tất cả mục này</button>
                            </div>
                            <table class="data-table">`;
                        
                        data[deviceKey].forEach((item, index) => {
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
    content = request.form.get('content', '').strip()
    user_code = request.form.get('user_code', '').strip()
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập Mã cá nhân trước khi gửi!'})
    
    if content:
        key = f"Mã cá nhân: {user_code} ({ip})"
        if key not in clipboard_data:
            clipboard_data[key] = []
        clipboard_data[key].insert(0, content)
        return jsonify({'status': 'ok'})
        
    return jsonify({'status': 'error', 'message': 'Nội dung không được để trống!'})

@app.route('/api/data')
def get_data():
    user_code = request.args.get('user_code', '').strip()
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Bạn phải nhập Mã cá nhân mới có thể xem/lấy dữ liệu!'})
    
    prefix = f"Mã cá nhân: {user_code} "
    filtered_data = {k: v for k, v in clipboard_data.items() if k.startswith(prefix)}
    
    return jsonify({'status': 'ok', 'data': filtered_data})

@app.route('/api/clear', methods=['POST'])
def clear_data():
    user_code = request.form.get('user_code', '').strip()
    
    if not user_code:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập Mã cá nhân!'})
    
    prefix = f"Mã cá nhân: {user_code} "
    keys_to_delete = [k for k in clipboard_data if k.startswith(prefix)]
    for k in keys_to_delete:
        del clipboard_data[k]
        
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
