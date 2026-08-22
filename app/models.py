import enum
from datetime import datetime
from app import db

# ==========================================
# 1. ENUMS (Chuẩn hóa trạng thái hệ thống)
# ==========================================
class RoleEnum(enum.Enum):
    CUSTOMER = "CUSTOMER"
    RESTAURANT = "RESTAURANT"
    ADMIN = "ADMIN"

class OrderStatusEnum(enum.Enum):
    PENDING = "PENDING"           # Chờ xác nhận
    CONFIRMED = "CONFIRMED"       # Đã xác nhận (Yêu cầu 5)
    PREPARING = "PREPARING"       # Đang chuẩn bị
    DELIVERING = "DELIVERING"     # Đang giao
    COMPLETED = "COMPLETED"       # Hoàn thành
    CANCELLED = "CANCELLED"       # Đã hủy

class PaymentMethodEnum(enum.Enum):
    CASH = "CASH"
    CREDIT_CARD = "CREDIT_CARD"
    E_WALLET = "E_WALLET"

class PaymentStatusEnum(enum.Enum):
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

# ==========================================
# 2. ABSTRACT BASE MODEL
# ==========================================
class BaseModel(db.Model):
    __abstract__ = True
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True) # Soft delete

# ==========================================
# 3. CORE ENTITIES
# ==========================================
class User(BaseModel):
    __tablename__ = 'users'
    
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    role = db.Column(db.Enum(RoleEnum), default=RoleEnum.CUSTOMER, nullable=False)
    
    # Phục vụ gợi ý món ăn (Vị trí, khẩu vị)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    taste_preferences = db.Column(db.Text, nullable=True) # Có thể lưu JSON string các tags
    
    # Relationships
    orders = db.relationship('Order', backref='customer', lazy=True)
    reviews = db.relationship('Review', backref='author', lazy=True)
    cart = db.relationship('Cart', backref='customer', uselist=False, lazy=True)

class Restaurant(BaseModel):
    __tablename__ = 'restaurants'
    
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True) # Yêu cầu 1: Tìm kiếm nhà hàng
    address = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Phục vụ gợi ý dựa trên vị trí
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    rating_avg = db.Column(db.Float, default=0.0)
    
    # Relationships
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
    
    # Phục vụ phân tích & gợi ý đi kèm
    flavor_tags = db.Column(db.String(255), nullable=True) 
    
    # Relationships
    reviews = db.relationship('Review', backref='dish', lazy=True)

# ==========================================
# 4. CART & ORDER MANAGEMENT (Yêu cầu 2, 3, 4)
# ==========================================
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
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='joined', cascade="all, delete-orphan")
    payment = db.relationship('Payment', backref='order', uselist=False, lazy=True)

class OrderItem(BaseModel):
    __tablename__ = 'order_items'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Numeric(10, 2), nullable=False) # Lưu giá tại thời điểm mua
    
    dish = db.relationship('Dish')

class Payment(BaseModel):
    __tablename__ = 'payments'
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    method = db.Column(db.Enum(PaymentMethodEnum), nullable=False)
    status = db.Column(db.Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING, nullable=False)
    transaction_id = db.Column(db.String(100), nullable=True, unique=True)

# ==========================================
# 5. REVIEWS & ANALYTICS 
# ==========================================
class Review(BaseModel):
    __tablename__ = 'reviews'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dish_id = db.Column(db.Integer, db.ForeignKey('dishes.id'), nullable=False, index=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=True) # Xác minh đã mua hàng
    
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=True)
    
    # Lưu kết quả phân tích bình luận (Tích cực, Tiêu cực, Trung tính)
    sentiment_score = db.Column(db.Float, nullable=True) 

    # Ràng buộc DB: Điểm rating từ 1-5
    __table_args__ = (
        db.CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
    )
    
if __name__ == "__main__":
    db.create_all()