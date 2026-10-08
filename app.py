import os
from flask import Flask, request, render_template_string, jsonify

app = Flask(__name__)

# Danh sách lưu trữ tài khoản theo thứ tự dòng (Mã số = STT 1, 2, 3...)
accounts_list = []

HTML_PAGE = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trạm Nhận Tài Khoản Theo Mã Số</title>
    <style>
        body { font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 20px auto; padding: 15px; background-color: #f4f6f9; }
        .card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.08); margin-bottom: 20px; }
        input[type="number"], textarea { width: 100%; padding: 10px; font-size: 16px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 5px; margin-bottom: 10px; }
        textarea { height: 140px; font-family: monospace; }
        button { padding: 10px 18px; font-size: 15px; cursor: pointer; background: #007bff; color: white; border: none; border-radius: 4px; font-weight: bold; }
        button:hover { opacity: 0.9; }
        .btn-success { background: #28a745; }
        .btn-danger { background: #dc3545; }
        .result-box { background: #e9f7ef; border: 1px solid #28a745; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 16px; color: #155724; display: none; margin-top: 15px; word-break: break-all; }
        .error-box { background: #f8d7da; border: 1px solid #dc3545; padding: 15px; border-radius: 5px; color: #721c24; display: none; margin-top: 15px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 14px; }
        th { background-color: #e9ecef; }
        .code-badge { background: #007bff; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; }
    </style>
</head>
<body>

    <!-- PHẦN DÀNH CHO NGƯỜI DÙNG / ĐIỆN THOẠI -->
    <div class="card">
        <h2>📱 Lấy Tài Khoản (Dành cho Người Dùng)</h2>
        <label><b>Nhập Mã Số của bạn (1, 2, 3...):</b></label>
        <input type="number" id="user-code" placeholder="Nhập mã số của bạn (ví dụ: 1)" min="1">
        <button onclick="getAccount()" class="btn-success">🔑 Lấy Tài Khoản</button>

        <div id="result" class="result-box"></div>
        <div id="error" class="error-box"></div>
    </div>

    <!-- PHẦN DÀNH CHO MÁY TÍNH / ADMIN -->
    <div class="card">
        <h2>💻 Quản Lý Danh Sách (Dành cho Admin)</h2>
        <label><b>Dán danh sách tài khoản (Mỗi dòng 1 tài khoản):</b></label>
        <textarea id="account-list" placeholder="Dán danh sách tài khoản vào đây, hệ thống sẽ TỰ ĐỘNG đánh mã số 1, 2, 3... từ trên xuống dưới:

user1@gmail.com|pass1
user2@gmail.com|pass2
user3@gmail.com|pass3"></textarea>
        <button onclick="saveAccounts()">💾 Lưu Danh Sách</button>
        <button onclick="clearAllData()" class="btn-danger" style="margin-left: 10px;">🗑️ Xóa Tất Cả</button>

        <h3 style="margin-top: 20px;">📋 Bảng Mã Số Hiện Có Trộn Hệ Thống:</h3>
        <div id="admin-table">Đang tải...</div>
    </div>

    <script>
        // Lấy tài khoản theo Mã Số
        function getAccount() {
            const code = document.getElementById('user-code').value.trim();
            const resBox = document.getElementById('result');
            const errBox = document.getElementById('error');

            resBox.style.display = 'none';
            errBox.style.display = 'none';

            if (!code) {
                alert('Vui lòng nhập mã số!');
                return;
            }

            fetch('/api/get-account', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'code=' + encodeURIComponent(code)
            })
            .then(res => res.json())
            .then(data => {
                if (data.status === 'ok') {
                    resBox.innerHTML = '<b>✅ Tài khoản thuộc Mã số ' + code + ':</b><br><br>' + data.account;
                    resBox.style.display = 'block';
                } else {
                    errBox.innerText = '❌ ' + data.message;
                    errBox.style.display = 'block';
                }
            });
        }

        // Lưu danh sách tài khoản từ Admin
        function saveAccounts() {
            const text = document.getElementById('account-list').value.trim();
            if (!text) return alert('Vui lòng dán danh sách tài khoản!');

            fetch('/api/save-accounts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: 'data=' + encodeURIComponent(text)
            })
            .then(res => res.json())
            .then(data => {
                alert(data.message);
                document.getElementById('account-list').value = '';
                loadAdminData();
            });
        }

        // Xóa sạch dữ liệu
        function clearAllData() {
            if (confirm('Bạn có chắc chắn muốn XÓA TẤT CẢ tài khoản không?')) {
                fetch('/api/clear', { method: 'POST' })
                    .then(res => res.json())
                    .then(data => {
                        loadAdminData();
                    });
            }
        }

        // Tải danh sách Admin
        function loadAdminData() {
            fetch('/api/admin-data')
                .then(res => res.json())
                .then(data => {
                    const container = document.getElementById('admin-table');
                    if (data.length === 0) {
                        container.innerHTML = '<p style="color: #777;">Chưa có tài khoản nào trong hệ thống.</p>';
                        return;
                    }

                    let html = '<table><tr><th style="width: 100px;">Mã Số</th><th>Nội Dung Tài Khoản</th></tr>';
                    data.forEach((acc, index) => {
                        html += `<tr>
                            <td><span class="code-badge">Mã số ${index + 1}</span></td>
                            <td>${acc}</td>
                        </tr>`;
                    });
                    html += '</table>';
                    container.innerHTML = html;
                });
        }

        loadAdminData();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_PAGE)

@app.route('/api/get-account', methods=['POST'])
def get_account():
    code_str = request.form.get('code', '').strip()
    if not code_str or not code_str.isdigit():
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập mã số bằng chữ số!'})
    
    code_num = int(code_str)
    if code_num < 1 or code_num > len(accounts_list):
        return jsonify({'status': 'error', 'message': f'Không tìm thấy Mã số {code_num}! (Hệ thống hiện chỉ có {len(accounts_list)} tài khoản)'})
    
    # Mã số 1 lấy phần tử đầu tiên (index 0)
    return jsonify({'status': 'ok', 'account': accounts_list[code_num - 1]})

@app.route('/api/save-accounts', methods=['POST'])
def save_accounts():
    raw_data = request.form.get('data', '').strip()
    if not raw_data:
        return jsonify({'status': 'error', 'message': 'Dữ liệu trống!'})

    # Tách từng dòng và đưa vào danh sách
    lines = [line.strip() for line in raw_data.split('\n') if line.strip()]
    accounts_list.extend(lines)

    return jsonify({'status': 'ok', 'message': f'Đã nạp thành công {len(lines)} tài khoản! Mã số tự động đánh từ {len(accounts_list) - len(lines) + 1} đến {len(accounts_list)}.'})

@app.route('/api/admin-data')
def admin_data():
    return jsonify(accounts_list)

@app.route('/api/clear', methods=['POST'])
def clear_data():
    accounts_list.clear()
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
