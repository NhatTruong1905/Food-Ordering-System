# Food Shoppe - Hệ Thống Đặt Món & Web Ẩm Thực Nhà Hàng Đối Tác

Dự án ứng dụng web đặt món được xây dựng bằng **Python Flask**, **Flask-SQLAlchemy**, **MySQL**, HTML5, CSS3 và JavaScript với thiết kế vintage sang trọng theo phong cách **Food Shoppe (Deli • Market • Catering)**.

---

## 📁 Cấu trúc Thư mục Dự án

```text
Food-Ordering-System/
├── .env                  # Cấu hình biến môi trường CSDL (DB_USER, DB_PASSWORD, DB_HOST, DB_NAME, DB_PORT...)
├── .env.example          # File mẫu cấu hình biến môi trường cho môi trường mới
├── requirements.txt      # Danh sách thư viện Python yêu cầu
├── README.md             # Tài liệu giới thiệu & Hướng dẫn sử dụng hệ thống
│
└── app/                  # Toàn bộ mã nguồn hệ thống
    ├── __init__.py       # Khởi tạo Flask app và cấu hình kết nối SQLAlchemy (mã hóa mật khẩu ký tự đặc biệt)
    ├── models.py         # 10 Models CSDL & Hàm nạp dữ liệu mẫu 20 nhà hàng thực tế kèm thực đơn seed_data()
    ├── dao.py            # Tầng Data Access Object: Tìm kiếm Tên/Địa chỉ, Phân trang, Lấy món ăn theo quán
    ├── index.py          # Tầng Controller: Khai báo Routes('/', '/api/restaurants', '/api/restaurants/<id>/dishes')
    ├── run.py            # Điểm khởi chạy chính của Server Flask
    │
    ├── templates/
    │   └── index.html    # Giao diện chính hiển thị Navbar, Danh sách Nhà hàng, Thực đơn động, Modal chi tiết
    │
    └── static/
        ├── css/
        │   └── style.css # Định dạng màu sắc vintage, layout 1440px, modal popup, thẻ nhà hàng, thẻ món ăn
        ├── js/
        │   └── main.js   # Tìm kiếm real-time, phân trang động, Modal chi tiết nhà hàng, nạp thực đơn món ăn
        └── images/
            ├── logo.svg           # Logo vector Food Shoppe
            ├── storefront.jpg     # Hình ảnh mặt tiền nhà hàng
            └── interior_tour.jpg  # Hình ảnh tour tham quan bên trong
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