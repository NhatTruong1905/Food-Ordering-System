import enum
from datetime import datetime
from decimal import Decimal
from werkzeug.security import generate_password_hash
from app import db


class RoleEnum(enum.Enum):
    CUSTOMER = "CUSTOMER"
    RESTAURANT = "RESTAURANT"
    ADMIN = "ADMIN"

class OrderStatusEnum(enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class PaymentMethodEnum(enum.Enum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    E_WALLET = "E_WALLET"

class PaymentStatusEnum(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)


class User(BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    taste_preferences = db.Column(db.Text, nullable=True)

    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)
    cart = db.relationship('Cart', backref='customer', uselist=False, lazy=True)


class Restaurant(BaseModel):
    __tablename__ = 'restaurants'
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner = db.relationship('User', backref=db.backref('restaurants', lazy=True))
    name = db.Column(db.String(100), nullable=False, index=True)
    address = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)

    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    rating_avg = db.Column(db.Float, default=0.0)

    dishes = db.relationship('Dish', backref='restaurant', lazy='dynamic')
    orders = db.relationship('Order', backref='restaurant', lazy='dynamic')


class Category(BaseModel):
    __tablename__ = 'categories'
    name = db.Column(db.String(50), nullable=False, unique=True)
    dishes = db.relationship('Dish', backref='category', lazy=True)


class Dish(BaseModel):
    __tablename__ = 'dishes'
    
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    
    name = db.Column(db.String(150), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    image_url = db.Column(db.String(255), nullable=True)

    flavor_tags = db.Column(db.String(255), nullable=True) 

    reviews = db.relationship('Review', backref='dish', lazy=True)


class Cart(BaseModel):
    __tablename__ = 'carts'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    items = db.relationship('CartItem', backref='cart', lazy='joined', cascade="all, delete-orphan")


class CartItem(BaseModel):
    __tablename__ = 'cart_items'
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False, index=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    dish = db.relationship('Dish')


class Order(BaseModel):
    __tablename__ = 'orders'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING, nullable=False, index=True)
    delivery_address = db.Column(db.String(255), nullable=False)

    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True)


class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False)
    
    dish = db.relationship('Dish')


class Payment(BaseModel):
    __tablename__ = 'payments'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.Enum(PaymentMethodEnum), nullable=False)
    status = db.Column(db.Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)


class Review(BaseModel):
    __tablename__ = 'reviews'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True)
    
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)

    sentiment_score = db.Column(db.Float, nullable=True) 

    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )


def seed_data():
    Review.query.delete()
    Payment.query.delete()
    OrderItem.query.delete()
    Order.query.delete()
    CartItem.query.delete()
    Cart.query.delete()
    Dish.query.delete()
    Category.query.delete()
    Restaurant.query.delete()
    User.query.delete()
    db.session.commit()

    default_password = generate_password_hash("123456")

    admin_user = User(
        username="admin",
        password_hash=default_password,
        email="admin@foodshoppe.vn",
        phone="0901000001",
        role=RoleEnum.ADMIN,
        latitude=10.776889,
        longitude=106.700806,
        taste_preferences="Tất cả các món"
    )

    customer_an = User(
        username="customer_an",
        password_hash=default_password,
        email="an.nguyen@gmail.com",
        phone="0903000004",
        role=RoleEnum.CUSTOMER,
        latitude=10.772540,
        longitude=106.698020,
        taste_preferences="cay, đậm đà, thích thịt bò, pizza, steak"
    )

    customer_binh = User(
        username="customer_binh",
        password_hash=default_password,
        email="binh.tran@gmail.com",
        phone="0903000005",
        role=RoleEnum.CUSTOMER,
        latitude=10.785620,
        longitude=106.695430,
        taste_preferences="ăn chay, thanh đạm, ít dầu mỡ, nhiều rau, organic"
    )

    customer_chi = User(
        username="customer_chi",
        password_hash=default_password,
        email="chi.le@gmail.com",
        phone="0903000006",
        role=RoleEnum.CUSTOMER,
        latitude=10.768910,
        longitude=106.692340,
        taste_preferences="sushi, hải sản tươi sống, dimsum, món thái"
    )

    db.session.add_all([admin_user, customer_an, customer_binh, customer_chi])
    db.session.flush()

    restaurants_data = [
        {
            "username": "owner_deli",
            "email": "deli@foodshoppe.vn",
            "phone": "0902000001",
            "name": "Food Shoppe Deli & Market",
            "address": "12 Lê Lợi, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Thực phẩm Deli tươi ngon, thịt nguội cao cấp, sandwiches hảo hạng và các món phong cách Âu truyền thống.",
            "image_url": "/static/images/storefront.jpg",
            "lat": 10.779782, "lng": 106.699018, "rating": 4.8
        },
        {
            "username": "owner_greengarden",
            "email": "contact@greengarden.vn",
            "phone": "0902000002",
            "name": "Green Garden Healthy Bistro",
            "address": "45 Trương Định, Phường 6, Quận 3, TP.HCM",
            "description": "Chuyên các món ăn dinh dưỡng, thực đơn thuần chay, nguyên liệu organic hữu cơ chuẩn quốc tế trong không gian xanh mát.",
            "image_url": "/static/images/interior_tour.jpg",
            "lat": 10.783450, "lng": 106.691230, "rating": 4.6
        },
        {
            "username": "owner_pizza4ps",
            "email": "benthanh@pizza4ps.com",
            "phone": "0902000003",
            "name": "Pizza 4P's Bến Thành",
            "address": "8 Thủ Khoa Huân, Phường Bến Thành, Quận 1, TP.HCM",
            "description": "Pizza nướng lò củi thủ công chuẩn vị Ý kết hợp phô mai tươi tự sản xuất tại Đà Lạt và ẩm thực Nhật Bản tinh tế.",
            "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=600",
            "lat": 10.773520, "lng": 106.697840, "rating": 4.9
        },
        {
            "username": "owner_comnieu",
            "email": "info@comnieusaigon.com.vn",
            "phone": "0902000004",
            "name": "Cơm Niêu Sài Gòn",
            "address": "27 Tú Xương, Phường Võ Thị Sáu, Quận 3, TP.HCM",
            "description": "Tinh hoa ẩm thực Việt Nam với màn trình diễn cơm đập giòn rụm, cá bống kho tộ và các món đồng quê dân dã đậm đà.",
            "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600",
            "lat": 10.782110, "lng": 106.687420, "rating": 4.7
        },
        {
            "username": "owner_hokkaido",
            "email": "booking@hokkaidosachi.com.vn",
            "phone": "0902000005",
            "name": "Sushi Hokkaido Sachi",
            "address": "139 Nguyễn Trãi, Phường Bến Thành, Quận 1, TP.HCM",
            "description": "Hải sản tươi sống nhập khẩu trực tiếp từ vùng biển Hokkaido Nhật Bản cùng nghệ thuật Sashimi và Sushi đỉnh cao.",
            "image_url": "https://images.unsplash.com/photo-1578474846511-04ba529f0b88?w=600",
            "lat": 10.770850, "lng": 106.691760, "rating": 4.8
        },
        {
            "username": "owner_dimtutac",
            "email": "dongdu@dimtutac.com",
            "phone": "0902000006",
            "name": "Dim Tu Tac Restaurant",
            "address": "55 Đông Du, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Ẩm thực Quảng Đông đương đại với hơn 100 món Dimsum thủ công nóng hổi và vịt quay Bắc Kinh da giòn thượng hạng.",
            "image_url": "https://images.unsplash.com/photo-1552566626-52f8b828add9?w=600",
            "lat": 10.776140, "lng": 106.704230, "rating": 4.7
        },
        {
            "username": "owner_thedeck",
            "email": "info@thedecksaigon.com",
            "phone": "0902000007",
            "name": "The Deck Saigon",
            "address": "38 Nguyễn Ư Dĩ, Phường Thảo Điền, TP. Thủ Đức, TP.HCM",
            "description": "Nhà hàng ven sông Sài Gòn sang trọng bậc nhất phục vụ ẩm thực Pan-Asian hiện đại và cocktail hoàng hôn lãng mạn.",
            "image_url": "https://images.unsplash.com/photo-1537047902294-62a40c20a6ae?w=600",
            "lat": 10.806450, "lng": 106.736820, "rating": 4.8
        },
        {
            "username": "owner_elgaucho",
            "email": "saigon@elgaucho.asia",
            "phone": "0902000008",
            "name": "El Gaucho Argentinian Steakhouse",
            "address": "74 Hai Bà Trưng, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Bò bít tết hảo hạng nướng than hoa phong cách Argentina nguyên bản cùng bộ sưu tập rượu vang quốc tế danh tiếng.",
            "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
            "lat": 10.778230, "lng": 106.703410, "rating": 4.9
        },
        {
            "username": "owner_hum",
            "email": "contact@humvietnam.com",
            "phone": "0902000009",
            "name": "Hum Vegetarian Lounge & Restaurant",
            "address": "32 Võ Văn Tần, Phường Võ Thị Sáu, Quận 3, TP.HCM",
            "description": "Không gian ẩm thực chay thanh tịnh, sáng tạo kết hợp thảo mộc thiên nhiên và các món ăn giàu dinh dưỡng cho sức khỏe.",
            "image_url": "https://images.unsplash.com/photo-1590846406792-0adc7f938f1d?w=600",
            "lat": 10.777920, "lng": 106.691450, "rating": 4.9
        },
        {
            "username": "owner_phothin",
            "email": "phothin.saigon@gmail.com",
            "phone": "0902000010",
            "name": "Phở Thìn Lò Đúc - Chi Nhánh Sài Gòn",
            "address": "110 Hai Bà Trưng, Phường Đa Kao, Quận 1, TP.HCM",
            "description": "Thương hiệu phở bò tái lăn trứ danh Hà Nội với nước dùng béo ngậy, ngập tràn hành lá tươi và thịt bò xào lửa lớn thơm nức.",
            "image_url": "https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=600",
            "lat": 10.784530, "lng": 106.698940, "rating": 4.5
        },
        {
            "username": "owner_secretgarden",
            "email": "secretgarden.saigon@gmail.com",
            "phone": "0902000011",
            "name": "Secret Garden Home-cooked Vietnamese",
            "address": "158 Pasteur, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Quán ăn sân thượng đậm chất thôn quê Việt Nam mộc mạc giữa lòng phố thị với các món cơm nhà gia đình thân thuộc.",
            "image_url": "https://images.unsplash.com/photo-1525610553991-2bede1a236e2?w=600",
            "lat": 10.778940, "lng": 106.697850, "rating": 4.6
        },
        {
            "username": "owner_bepmein",
            "email": "bepmein@gmail.com",
            "phone": "0902000012",
            "name": "Bếp Mẹ Ỉn - Authentic Vietnamese Street Food",
            "address": "136 Lê Thánh Tôn, Phường Bến Thành, Quận 1, TP.HCM",
            "description": "Đạt giải thưởng Michelin Bib Gourmand với món bánh xèo tôm nhảy giòn rụm, cơm chiên trái dừa và gà nướng ống tre.",
            "image_url": "https://images.unsplash.com/photo-1466978913421-dad2ebd01d17?w=600",
            "lat": 10.772980, "lng": 106.698420, "rating": 4.7
        },
        {
            "username": "owner_gyushige",
            "email": "hotro@gyushige.com.vn",
            "phone": "0902000013",
            "name": "Gyu-Shige Yakiniku Ngưu Phồn",
            "address": "119 Hồ Tùng Mậu, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Thương hiệu nướng than hoa Yakiniku Nhật Bản với các phần thịt bò Wagyu, dẻ sườn ướp sốt Miso đặc quyền hảo vị.",
            "image_url": "https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=600",
            "lat": 10.773120, "lng": 106.703890, "rating": 4.6
        },
        {
            "username": "owner_pastafresca",
            "email": "thaodien@pastafresca.vn",
            "phone": "0902000014",
            "name": "Pasta Fresca Thảo Điền",
            "address": "28 Thảo Điền, Phường Thảo Điền, TP. Thủ Đức, TP.HCM",
            "description": "Mì Ý tươi sợi thủ công cán trong ngày kết hợp cùng sốt Pesto béo thơm, sốt bò bằm Bolognese và phô mai Burrata tươi ngậy.",
            "image_url": "https://images.unsplash.com/photo-1559339352-11d035aa65de?w=600",
            "lat": 10.803420, "lng": 106.732150, "rating": 4.7
        },
        {
            "username": "owner_chaygarden",
            "email": "chaygarden.vovantan@gmail.com",
            "phone": "0902000015",
            "name": "Chay Garden Vegetarian Restaurant & Coffee",
            "address": "52 Võ Văn Tần, Phường Võ Thị Sáu, Quận 3, TP.HCM",
            "description": "Biệt thự cổ phong cách Đông Dương lãng mạn phục vụ các món chay thuần khiết, trà sen hữu cơ và đồ tráng miệng thanh mát.",
            "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600",
            "lat": 10.776510, "lng": 106.689720, "rating": 4.8
        },
        {
            "username": "owner_sanfulou",
            "email": "sanfulou@d1-concepts.com",
            "phone": "0902000016",
            "name": "San Fu Lou Cantonese Kitchen",
            "address": "76A Lê Lai, Phường Bến Thành, Quận 1, TP.HCM",
            "description": "Bếp mở chuẩn phong cách Hong Kong với mì kéo tươi truyền thống, há cảo sò điệp bó xôi và vịt quay thơm lừng.",
            "image_url": "https://images.unsplash.com/photo-1508424757105-b6d5ad9329d0?w=600",
            "lat": 10.770920, "lng": 106.695310, "rating": 4.6
        },
        {
            "username": "owner_tokyodeli",
            "email": "phanxichlong@tokyodeli.com.vn",
            "phone": "0902000017",
            "name": "Tokyo Deli Sushi",
            "address": "240 Phan Xích Long, Phường 2, Quận Phú Nhuận, TP.HCM",
            "description": "Chuỗi ẩm thực Nhật Bản quen thuộc với thực đơn đa dạng từ Sushi, Sashimi, Set Lunch Bento văn phòng đến lẩu ấm cúng.",
            "image_url": "https://images.unsplash.com/photo-1611143669185-af224c5e3252?w=600",
            "lat": 10.796340, "lng": 106.689450, "rating": 4.4
        },
        {
            "username": "owner_marukame",
            "email": "marukame.vietnam@toridoll.com",
            "phone": "0902000018",
            "name": "Marukame Udon",
            "address": "215 Lý Tự Trọng, Phường Bến Thành, Quận 1, TP.HCM",
            "description": "Mì Udon tươi truyền thống vùng Sanuki Nhật Bản luộc tươi trực tiếp trước mặt khách cùng quầy Tempura vàng rụm tự chọn.",
            "image_url": "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=600",
            "lat": 10.772180, "lng": 106.694820, "rating": 4.5
        },
        {
            "username": "owner_quanbui",
            "email": "info@quan-bui.com",
            "phone": "0902000019",
            "name": "Quán Bụi - Vietnamese Bistro",
            "address": "19 Ngô Văn Năm, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Ẩm thực ba miền Việt Nam chuẩn vị gia đình không bột ngọt, phong cách Đông Dương hoài cổ và ấm áp.",
            "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=600",
            "lat": 10.781250, "lng": 106.705120, "rating": 4.7
        },
        {
            "username": "owner_tuktuk",
            "email": "tuktuk.bistro@gmail.com",
            "phone": "0902000020",
            "name": "TukTuk Thai Bistro",
            "address": "38 Lý Tự Trọng, Phường Bến Nghé, Quận 1, TP.HCM",
            "description": "Ẩm thực đường phố Thái Lan biến tấu phong cách hiện đại với súp Tomyum chua cay, gỏi đu đủ Somtum và xôi xoài ngọt ngào.",
            "image_url": "https://images.unsplash.com/photo-1544025162-d76694265947?w=600",
            "lat": 10.777420, "lng": 106.701850, "rating": 4.6
        }
    ]

    created_restaurants = []
    for item in restaurants_data:
        owner = User(
            username=item["username"],
            password_hash=default_password,
            email=item["email"],
            phone=item["phone"],
            role=RoleEnum.RESTAURANT,
            latitude=item["lat"],
            longitude=item["lng"],
            taste_preferences="Chủ nhà hàng ẩm thực"
        )
        db.session.add(owner)
        db.session.flush()

        res = Restaurant(
            owner_id=owner.id,
            name=item["name"],
            address=item["address"],
            description=item["description"],
            image_url=item.get("image_url"),
            latitude=item["lat"],
            longitude=item["lng"],
            rating_avg=item["rating"]
        )
        db.session.add(res)
        db.session.flush()
        created_restaurants.append(res)

    categories = [
        Category(name="Món Khai Vị & Salad"),
        Category(name="Món Chính Đặc Sắc"),
        Category(name="Pizza & Mì Ý"),
        Category(name="Sushi & Sashimi"),
        Category(name="Dimsum & Món Hoa"),
        Category(name="Món Chay & Healthy"),
        Category(name="Món Nướng Yakiniku"),
        Category(name="Món Việt Truyền Thống"),
        Category(name="Món Thái Chua Cay"),
        Category(name="Đồ Uống & Tráng Miệng")
    ]
    db.session.add_all(categories)
    db.session.flush()

    cat_map = {c.name: c.id for c in categories}

    dishes = [
        Dish(
            restaurant_id=created_restaurants[0].id,
            category_id=cat_map["Món Khai Vị & Salad"],
            name="Smoked Salmon Caesar Salad",
            description="Salad cá hồi xông khói Na Uy sốt Caesar truyền thống, bánh mì nướng bơ tỏi giòn rụm và phô mai Parmesan.",
            price=Decimal("125000.00"),
            image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500",
            flavor_tags="ít béo, thanh mát, cá hồi, phô mai"
        ),
        Dish(
            restaurant_id=created_restaurants[0].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Classic Pastrami Reuben Sandwich",
            description="Bánh mì kẹp thịt bò muối Pastrami nướng giòn kèm phô mai Thụy Sĩ chảy, dưa cải chua New York.",
            price=Decimal("165000.00"),
            image_url="https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=500",
            flavor_tags="đậm đà, thịt bò, béo ngậy, cay nhẹ"
        ),
        Dish(
            restaurant_id=created_restaurants[0].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Truffle Roast Beef Panini",
            description="Bánh Panini nướng bơ kẹp thịt bò nướng tảng sốt dầu nấm Truffle quý tộc.",
            price=Decimal("185000.00"),
            image_url="https://images.unsplash.com/photo-1509722747041-616f39b57569?w=500",
            flavor_tags="bò nướng, nấm truffle, bánh mì"
        ),
        Dish(
            restaurant_id=created_restaurants[0].id,
            category_id=cat_map["Đồ Uống & Tráng Miệng"],
            name="New York Baked Cheesecake",
            description="Bánh phô mai nướng kiểu New York béo ngậy sốt dâu rừng chua ngọt.",
            price=Decimal("75000.00"),
            image_url="https://images.unsplash.com/photo-1533134242443-d4fd215305ad?w=500",
            flavor_tags="bánh ngọt, phô mai, dâu tây"
        ),

        Dish(
            restaurant_id=created_restaurants[1].id,
            category_id=cat_map["Món Chay & Healthy"],
            name="Buddha Bowl Hạt Quinoa Bơ Sáp",
            description="Tô dinh dưỡng hạt Quinoa cầu vồng, bơ sáp Đắk Lắk, đậu gà hữu cơ và sốt mè rang béo ngậy.",
            price=Decimal("115000.00"),
            image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
            flavor_tags="ăn chay, hạt quinoa, bơ sáp, healthy"
        ),
        Dish(
            restaurant_id=created_restaurants[1].id,
            category_id=cat_map["Món Chay & Healthy"],
            name="Gỏi Cuốn Nấm Ngũ Sắc Sốt Bơ Đậu Phộng",
            description="Bánh tráng gạo lứt cuộn nấm đùi gà áp chảo, rau mầm tươi mát chấm sốt bơ đậu phộng béo bùi.",
            price=Decimal("85000.00"),
            image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500",
            flavor_tags="thanh đạm, ít béo, rau củ"
        ),
        Dish(
            restaurant_id=created_restaurants[1].id,
            category_id=cat_map["Đồ Uống & Tráng Miệng"],
            name="Sinh Tố Xanh Detox Cải Kale & Táo",
            description="Cải xoăn Kale hữu cơ xay tươi cùng táo xanh New Zealand và hạt chia thanh lọc cơ thể.",
            price=Decimal("65000.00"),
            image_url="https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
            flavor_tags="detox, cải kale, sinh tố healthy"
        ),

        Dish(
            restaurant_id=created_restaurants[2].id,
            category_id=cat_map["Pizza & Mì Ý"],
            name="Pizza 4 Loại Phô Mai Kèm Mật Ong",
            description="Pizza 4 Cheese trứ danh với phô mai Camembert, Mozzarella, Gorgonzola tự sản xuất rưới mật ong thơm lừng.",
            price=Decimal("280000.00"),
            image_url="https://images.unsplash.com/photo-1513104890138-7c749659a591?w=500",
            flavor_tags="phô mai béo ngậy, ngọt dịu, nướng củi"
        ),
        Dish(
            restaurant_id=created_restaurants[2].id,
            category_id=cat_map["Pizza & Mì Ý"],
            name="Pizza Burrata Thịt Nguội Parma Ham",
            description="Phô mai tươi Burrata béo dẻo nguyên quả đặt trên nền thịt nguội Parma Ham Ý muối 24 tháng.",
            price=Decimal("320000.00"),
            image_url="https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=500",
            flavor_tags="burrata tươi, thịt nguội ý, đẳng cấp"
        ),
        Dish(
            restaurant_id=created_restaurants[2].id,
            category_id=cat_map["Pizza & Mì Ý"],
            name="Mì Ý Sốt Kem Cà Chua Thịt Cua Tươi",
            description="Spaghetti sợi dẻo sốt kem cà chua béo ngậy ngập tràn thịt cua biển tươi tách vỏ trong ngày.",
            price=Decimal("245000.00"),
            image_url="https://images.unsplash.com/photo-1621996346565-e3d5d628169b?w=500",
            flavor_tags="mì ý, thịt cua tươi, sốt kem"
        ),

        Dish(
            restaurant_id=created_restaurants[3].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Cơm Đập Niêu Đất Giòn Rụm",
            description="Niêu đất đập vỡ trình diễn lấy lớp cơm cháy vàng giòn rưới mỡ hành thơm nức mũi.",
            price=Decimal("45000.00"),
            image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
            flavor_tags="cơm cháy giòn, mỡ hành, truyền thống"
        ),
        Dish(
            restaurant_id=created_restaurants[3].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Cá Bống Trứng Kho Tộ Tiêu Xanh",
            description="Cá bống tươi đầy trứng kho keo nước dừa trong tộ đất cùng ớt hiểm và tiêu xanh cay nồng.",
            price=Decimal("165000.00"),
            image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
            flavor_tags="đậm đà, cá kho tộ, cay nhẹ"
        ),
        Dish(
            restaurant_id=created_restaurants[3].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Sườn Non Heo Nướng Mật Ong Rừng",
            description="Sườn non heo ướp mật ong rừng nguyên chất nướng than hoa vàng ruộm thơm lừng.",
            price=Decimal("175000.00"),
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            flavor_tags="sườn nướng, mật ong rừng, cơm niêu"
        ),

        Dish(
            restaurant_id=created_restaurants[4].id,
            category_id=cat_map["Sushi & Sashimi"],
            name="Sashimi Tuyệt Phẩm Hokkaido 5 Loại",
            description="Sashimi cá hồi tươi Na Uy, sò điệp Hotate, cá ngừ Akami, bạch tuộc và trứng cá hồi ngâm tương.",
            price=Decimal("495000.00"),
            image_url="https://images.unsplash.com/photo-1579871494447-9811cf80d66c?w=500",
            flavor_tags="tươi sống, ngọt tự nhiên, hải sản"
        ),
        Dish(
            restaurant_id=created_restaurants[4].id,
            category_id=cat_map["Sushi & Sashimi"],
            name="Salmon Aburi Cheese Roll (Cuộn Cá Hồi Khò)",
            description="Cơm cuộn cá hồi Na Uy khò lửa thơm lừng sốt kem phô mai chảy béo ngậy và trứng cá chuồn.",
            price=Decimal("185000.00"),
            image_url="https://images.unsplash.com/photo-1611143669185-af224c5e3252?w=500",
            flavor_tags="cá hồi khò lửa, phô mai, sushi"
        ),
        Dish(
            restaurant_id=created_restaurants[4].id,
            category_id=cat_map["Sushi & Sashimi"],
            name="Nigiri Bò Wagyu A5 Khò Sốt Ponzu",
            description="Thịt bò Wagyu A5 Nhật Bản vân mỡ cẩm thạch khò tái đặt trên cơm sushi dẻo thơm.",
            price=Decimal("210000.00"),
            image_url="https://images.unsplash.com/photo-1611143669185-af224c5e3252?w=500",
            flavor_tags="bò wagyu a5, nigiri sushi"
        ),

        Dish(
            restaurant_id=created_restaurants[5].id,
            category_id=cat_map["Dimsum & Món Hoa"],
            name="Há Cảo Tôm Tươi Thủy Tinh (4 viên)",
            description="Vỏ bánh trong suốt thấy rõ nhân tôm sú tươi giòn sần sật hấp nóng trong xửng tre.",
            price=Decimal("88000.00"),
            image_url="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
            flavor_tags="dimsum, tôm tươi, ngọt thanh"
        ),
        Dish(
            restaurant_id=created_restaurants[5].id,
            category_id=cat_map["Dimsum & Món Hoa"],
            name="Vịt Quay Bắc Kinh Da Giòn Thượng Hạng",
            description="Vịt quay da nâu cánh gián giòn rụm cuốn bánh tráng kèm dưa leo, đầu hành và sốt tương ngọt.",
            price=Decimal("480000.00"),
            image_url="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
            flavor_tags="vịt quay da giòn, sốt tương ngọt, quảng đông"
        ),
        Dish(
            restaurant_id=created_restaurants[5].id,
            category_id=cat_map["Dimsum & Món Hoa"],
            name="Bánh Bao Kim Sa Trứng Muối Tan Chảy",
            description="Bánh bao hấp nóng hổi nhân sốt bơ trứng muối thơm ngậy sánh mịn tan chảy khi bẻ đôi.",
            price=Decimal("68000.00"),
            image_url="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
            flavor_tags="bánh bao kim sa, trứng muối, dimsum"
        ),

        Dish(
            restaurant_id=created_restaurants[6].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Cua Lột Chiên Giòn Sốt Chanh Dây",
            description="Cua lột nguyên con tẩm bột chiên phồng giòn tan rưới sốt bơ chanh dây chua dịu.",
            price=Decimal("260000.00"),
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            flavor_tags="cua lột chiên giòn, sốt chanh dây"
        ),
        Dish(
            restaurant_id=created_restaurants[6].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Cá Chẽm Áp Chảo Sốt Bơ Thảo Mộc",
            description="Phi lê cá chẽm tươi áp chảo da giòn rụm, thịt cá ngọt mềm sốt bơ tỏi thì là.",
            price=Decimal("340000.00"),
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            flavor_tags="cá chẽm áp chảo, bơ thảo mộc, ven sông"
        ),
        Dish(
            restaurant_id=created_restaurants[7].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Black Angus Ribeye Steak 250g",
            description="Thăn bò Black Angus nướng than hoa Medium Rare kèm sốt tiêu đen Chimichurri kiểu Argentina.",
            price=Decimal("790000.00"),
            image_url="https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=500",
            flavor_tags="thịt bò hảo hạng, thơm khói than hoa, đậm đà"
        ),
        Dish(
            restaurant_id=created_restaurants[7].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Wagyu Filet Mignon 200g",
            description="Thịt bò Wagyu vân mỡ tuyệt hảo nướng mềm mọng như bơ tan trong miệng.",
            price=Decimal("1250000.00"),
            image_url="https://images.unsplash.com/photo-1600891964599-f61ba0e24092?w=500",
            flavor_tags="bò wagyu, bít tết thượng hạng"
        ),

        Dish(
            restaurant_id=created_restaurants[8].id,
            category_id=cat_map["Món Chay & Healthy"],
            name="Cơm Chiên Gạo Lứt Hạt Sen Lá Sen",
            description="Gạo lứt thơm dẻo xào cùng hạt sen Huế, nấm đông cô tươi bọc trong lá sen hấp thanh khiết.",
            price=Decimal("135000.00"),
            image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
            flavor_tags="ăn chay, thanh đạm, ít dầu mỡ, nhiều chất xơ"
        ),
        Dish(
            restaurant_id=created_restaurants[8].id,
            category_id=cat_map["Món Chay & Healthy"],
            name="Gỏi Nấm Tràm Thảo Mộc Chua Ngọt",
            description="Nấm tràm Phú Quốc dai giòn bóp gỏi rau răm, hoa chuối và đậu phộng rang.",
            price=Decimal("120000.00"),
            image_url="https://images.unsplash.com/photo-1540420773420-3366772f4999?w=500",
            flavor_tags="gỏi nấm, thảo mộc, chua ngọt"
        ),

        Dish(
            restaurant_id=created_restaurants[9].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Phở Bò Tái Lăn Đặc Biệt Ngập Hành",
            description="Bát phở bò tái lăn trứ danh xào lửa lớn thơm mùi khói, nước dùng ngọt tủy đậm đà ngập tràn hành hoa.",
            price=Decimal("90000.00"),
            image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=500",
            flavor_tags="phở tái lăn, hành hoa, nước béo đậm đà"
        ),
        Dish(
            restaurant_id=created_restaurants[9].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Quẩy Giòn Hà Nội (Đĩa 3 chiếc)",
            description="Quẩy chiên vàng ruộm giòn tan chấm nước dùng phở bò nóng hổi.",
            price=Decimal("15000.00"),
            image_url="https://images.unsplash.com/photo-1582878826629-29b7ad1cdc43?w=500",
            flavor_tags="quẩy giòn, ăn kèm phở"
        ),

        Dish(
            restaurant_id=created_restaurants[10].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Thịt Ba Rọi Kho Trứng Cút Nước Dừa",
            description="Thịt ba rọi mềm rục béo ngậy kho cùng trứng cút trong nước dừa xiêm Bến Tre ngả màu cánh gián.",
            price=Decimal("135000.00"),
            image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
            flavor_tags="thịt kho tàu, nước dừa, cơm nhà"
        ),

        Dish(
            restaurant_id=created_restaurants[11].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Bánh Xèo Tôm Nhảy Vỏ Giòn Michelin",
            description="Bánh xèo miền Tây tôm sông tươi nhảy tanh tách, vỏ mỏng giòn rụm cuốn rau rừng bánh tráng.",
            price=Decimal("110000.00"),
            image_url="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
            flavor_tags="bánh xèo giòn, tôm nhảy, michelin"
        ),

        Dish(
            restaurant_id=created_restaurants[12].id,
            category_id=cat_map["Món Nướng Yakiniku"],
            name="Dẻ Sườn Bò Mỹ Ướp Sốt Miso Đặc Quyền",
            description="Dẻ sườn bò Mỹ đan xen vân mỡ nướng than hoa Yakiniku chín vàng mọng nước chấm sốt tương Nhật.",
            price=Decimal("230000.00"),
            image_url="https://images.unsplash.com/photo-1555939594-58d7cb561ad1?w=500",
            flavor_tags="bò nướng yakiniku, sốt miso, thịt nướng than"
        ),

        Dish(
            restaurant_id=created_restaurants[13].id,
            category_id=cat_map["Pizza & Mì Ý"],
            name="Mì Ý Tagliatelle Tươi Sốt Bolognese",
            description="Sợi mì tươi cán thủ công trong ngày hòa quyện sốt thịt bò bằm Bolognese nấu chậm 4 tiếng.",
            price=Decimal("195000.00"),
            image_url="https://images.unsplash.com/photo-1621996346565-e3d5d628169b?w=500",
            flavor_tags="mì ý tươi, sốt bolognese bò bằm"
        ),

        Dish(
            restaurant_id=created_restaurants[14].id,
            category_id=cat_map["Món Chay & Healthy"],
            name="Đậu Hũ Non Sốt Trái Lựu Chua Ngọt",
            description="Đậu hũ non chiên giòn áo lớp sốt nước ép quả lựu đỏ tự nhiên thanh tao giải nhiệt.",
            price=Decimal("105000.00"),
            image_url="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=500",
            flavor_tags="đậu hũ non, sốt lựu, món chay đông dương"
        ),

        Dish(
            restaurant_id=created_restaurants[15].id,
            category_id=cat_map["Dimsum & Món Hoa"],
            name="Mì Kéo Tay Xá Xíu Quảng Đông Sốt Dầu Hào",
            description="Mì trứng kéo tay thủ công dai mềm ăn kèm thịt xá xíu mật ong nướng thơm phức.",
            price=Decimal("125000.00"),
            image_url="https://images.unsplash.com/photo-1563245372-f21724e3856d?w=500",
            flavor_tags="mì kéo tươi, xá xíu mật ong, hongkong"
        ),

        Dish(
            restaurant_id=created_restaurants[16].id,
            category_id=cat_map["Sushi & Sashimi"],
            name="Set Bento Cá Hồi Sốt Teriyaki",
            description="Cơm Bento dinh dưỡng gồm cá hồi Na Uy áp chảo sốt Teriyaki, trứng cuộn, salad mè và canh miso.",
            price=Decimal("135000.00"),
            image_url="https://images.unsplash.com/photo-1611143669185-af224c5e3252?w=500",
            flavor_tags="bento cá hồi, sốt teriyaki, nhật bản"
        ),

        Dish(
            restaurant_id=created_restaurants[17].id,
            category_id=cat_map["Món Chính Đặc Sắc"],
            name="Mì Udon Bò Kake Nước Dùng Dashi",
            description="Sợi mì Udon tươi dày dẻo Sanuki trứ danh ngập trong nước dùng Dashi thanh ngọt kèm thịt bò thái lát mềm.",
            price=Decimal("89000.00"),
            image_url="https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500",
            flavor_tags="mì udon sanuki, thịt bò, dashi nhật"
        ),
        Dish(
            restaurant_id=created_restaurants[17].id,
            category_id=cat_map["Món Khai Vị & Salad"],
            name="Tempura Tôm Sú Khổng Lồ Chiên Giòn",
            description="Tôm sú tươi tẩm bột xù Tempura chiên vàng rụm chấm nước tương gừng củ cải.",
            price=Decimal("35000.00"),
            image_url="https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=500",
            flavor_tags="tempura tôm giòn rụm"
        ),

        Dish(
            restaurant_id=created_restaurants[18].id,
            category_id=cat_map["Món Việt Truyền Thống"],
            name="Chả Giò Quán Bụi Hải Sản Đặc Biệt",
            description="Chả giò tôm cua thịt cuốn bánh tráng rế chiên giòn tan chấm nước mắm chua ngọt chuẩn vị.",
            price=Decimal("125000.00"),
            image_url="https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=500",
            flavor_tags="chả giò hải sản, giòn tan"
        ),

        Dish(
            restaurant_id=created_restaurants[19].id,
            category_id=cat_map["Món Thái Chua Cay"],
            name="Súp Tomyum Hải Sản Nước Cốt Dừa",
            description="Súp tôm sú, mực tươi nấu cùng củ riềng, lá chúc, sả cây và nước cốt dừa chua cay chuẩn vị Bangkok.",
            price=Decimal("175000.00"),
            image_url="https://images.unsplash.com/photo-1544025162-d76694265947?w=500",
            flavor_tags="súp tomyum, chua cay, cốt dừa béo"
        ),
        Dish(
            restaurant_id=created_restaurants[19].id,
            category_id=cat_map["Đồ Uống & Tráng Miệng"],
            name="Xôi Xoài Nước Cốt Dừa Thái Lan",
            description="Xôi nếp dẻo thơm rưới nước cốt dừa mặn ngọt ăn kèm xoài chín vàng ngọt lịm.",
            price=Decimal("85000.00"),
            image_url="https://images.unsplash.com/photo-1556881286-fc6915169721?w=500",
            flavor_tags="xôi xoài, nước cốt dừa, món thái"
        )
    ]
    db.session.add_all(dishes)
    db.session.flush()

    cart_an = Cart(user_id=customer_an.id)
    cart_binh = Cart(user_id=customer_binh.id)
    db.session.add_all([cart_an, cart_binh])
    db.session.flush()

    cart_item1 = CartItem(cart_id=cart_an.id, dish_id=dishes[7].id, quantity=1)
    db.session.add(cart_item1)

    order1 = Order(
        user_id=customer_an.id,
        restaurant_id=created_restaurants[2].id,
        total_amount=Decimal("280000.00"),
        status=OrderStatusEnum.COMPLETED,
        delivery_address="Toà nhà Bitexco, 2 Hải Triều, Bến Nghé, Quận 1, TP.HCM"
    )
    db.session.add(order1)
    db.session.flush()

    order_item1 = OrderItem(order_id=order1.id, dish_id=dishes[7].id, quantity=1,
                            price_at_purchase=Decimal("280000.00"))
    payment1 = Payment(
        order_id=order1.id,
        amount=Decimal("280000.00"),
        method=PaymentMethodEnum.E_WALLET,
        status=PaymentStatusEnum.SUCCESS,
        transaction_id="MOMO_PAY_2026082701"
    )
    review1 = Review(
        user_id=customer_an.id,
        dish_id=dishes[7].id,
        order_id=order1.id,
        rating=5,
        comment="Pizza 4 phô mai ăn cùng mật ong cực kỳ xuất sắc, vỏ bánh thơm mùi củi!",
        sentiment_score=0.98
    )

    db.session.add_all([order_item1, payment1, review1])
    db.session.commit()


if __name__ == "__main__":
    import os
    import sys

    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    PARENT_DIR = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
    if PARENT_DIR not in sys.path:
        sys.path.insert(0, PARENT_DIR)
    if CURRENT_DIR not in sys.path:
        sys.path.insert(0, CURRENT_DIR)

    try:
        from app import app
    except ImportError:
        from __init__ import app

    with app.app_context():
        db.create_all()
        seed_data()
