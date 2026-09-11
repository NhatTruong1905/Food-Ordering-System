# Food Shoppe - Hệ Thống Đặt Món & Web Ẩm Thực Nhà Hàng Đối Tác

Dự án ứng dụng web đặt món được xây dựng bằng **Python Flask**, **Flask-SQLAlchemy**, **MySQL**, HTML5, CSS3 và JavaScript với thiết kế vintage sang trọng theo phong cách **Food Shoppe (Deli • Market • Catering)**.

---

## 📁 Cấu trúc Thư mục Dự án

```text
Food-Ordering-System/
├── .env
├── .env.example
├── requirements.txt
├── README.md
│
└── app/
    ├── __init__.py
    ├── models.py
    ├── dao.py
    ├── index.py
    ├── run.py
    ├── utils.py
    ├── vnpay.py
    │
    ├── templates/
    │   └── index.html
    │
    └── static/
        ├── css/
        │   └── style.css
        ├── js/
        │   └── main.js
        └── images/
            ├── logo.svg
            ├── storefront.jpg
            └── interior_tour.jpg
```

---

## ⚙️ Cấu hình Biến Môi Trường (`.env`)

Tạo file `.env` tại thư mục gốc của dự án với các thông số kết nối MySQL:

```env
DB_USER=root
DB_PASSWORD=root@123
DB_HOST=localhost
DB_PORT=3306
DB_NAME=food_ordering_db
SECRET_KEY=supersecretkey_food_ordering_2026
```

*(Lưu ý: Mật khẩu có ký tự đặc biệt như `@`, `#`, `%` được hệ thống tự động mã hóa an toàn qua `urllib.parse.quote_plus` trong `app/__init__.py`)*.

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Cài đặt các thư viện phụ thuộc
```bash
pip install -r requirements.txt
```

### 2. Tạo bảng CSDL & Nạp dữ liệu mẫu 20 Nhà Hàng + Thực Đơn (Seed Data)
Chạy file `models.py` để tự động tạo 10 bảng và nạp 20 nhà hàng thực tế tại TP.HCM kèm danh sách món ăn:
```bash
python -m app.models
```
*(hoặc: `python app/models.py`)*

### 3. Khởi chạy Server Web Flask
Chạy file `run.py` bên trong package `app/`:
```bash
python -m app.run
```
*(hoặc: `python app/run.py`)*

### 4. Mở trên trình duyệt
Truy cập đường dẫn:
```
http://127.0.0.1:5000
```

---