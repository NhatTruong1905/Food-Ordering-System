# Food Shoppe - Hệ Thống Đặt Món & Web Deli Market

Dự án giao diện web được xây dựng bằng **Python Flask**, HTML5, CSS3 và JavaScript với thiết kế vintage sang trọng theo phong cách **Food Shoppe (Deli • Market • Catering)**.

---

## 📁 Cấu trúc Thư mục

```text
Food-Ordering-System/
│
├── init.py               # File chính khởi chạy Flask server và cấu hình API
├── app.py                # File runner phụ trợ (có thể chạy `python app.py`)
├── requirements.txt      # Thư viện yêu cầu (Flask)
├── README.md             # Hướng dẫn sử dụng
│
├── templates/
│   └── index.html        # Giao diện chính hiển thị Deli Menu, Storefront, Virtual Tour & Đặt hàng
│
└── static/
    ├── css/
    │   └── style.css     # Định dạng phong cách màu sắc, hiệu ứng và responsive layout
    ├── js/
    │   └── main.js       # Xử lý tương tác Modal, Toast thông báo, Đặt món qua API
    └── images/
        ├── logo.svg           # Logo SVG Food Shoppe
        ├── storefront.jpg     # Hình ảnh mặt tiền cửa hàng
        └── interior_tour.jpg  # Hình ảnh tour tham quan bên trong cửa hàng
```

---

## 🚀 Hướng dẫn Chạy Ứng dụng

### 1. Cài đặt thư viện (nếu chưa cài)
```bash
pip install -r requirements.txt
```

### 2. Chạy Flask Server
Bạn có thể chạy bằng một trong hai cách:

```bash
python init.py
```
*hoặc:*
```bash
python app.py
```

### 3. Mở trên trình duyệt
Truy cập đường dẫn:
```
http://127.0.0.1:5000
```

---

## ✨ Tính năng Nổi bật
- **Thiết kế theo chuẩn mẫu hình ảnh**: Tái hiện chính xác thanh điều hướng nâu gỗ, khung logo sang trọng, bố cục 2 cột với sidebar mặt tiền và khu vực tour ảo.
- **Tour tham quan ảo 360° (Virtual Tour)**: Xem hình ảnh không gian bên trong quán và đặt bàn trực tiếp.
- **Menu đặc sản trong ngày (Daily Specials)**: Danh sách món ăn kèm thẻ giá, phân loại và nút đặt món nhanh.
- **Tích hợp API Flask (`/api/order` & `/api/specials`)**: Gửi yêu cầu đặt hàng và nhận mã đơn hàng thời gian thực kèm thông báo Toast.
- **Tương thích mọi thiết bị (Responsive)**: Hiển thị tối ưu từ điện thoại di động đến máy tính để bàn.
