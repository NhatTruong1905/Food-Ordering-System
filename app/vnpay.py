import os
import hmac
import hashlib
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(override=True)

VNPAY_TMN_CODE = os.getenv('VNPAY_TMN_CODE') or os.getenv('vnp_TmnCode') or 'JKYF5BUS'
VNPAY_HASH_SECRET = os.getenv('VNPAY_HASH_SECRET') or os.getenv('vnp_HashSecret') or '1NJEQK1N1WLBMZL9EI0JHWH0YI44M7OT'
VNPAY_URL = os.getenv('VNPAY_URL') or os.getenv('vnp_Url') or 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNPAY_RETURN_URL = os.getenv('VNPAY_RETURN_URL') or os.getenv('vnp_ReturnUrl') or 'http://127.0.0.1:5000/vnpay_return'

VNPAY_RESPONSE_CODES = {
    '00': 'Giao dịch thành công',
    '07': 'Trừ tiền thành công. Giao dịch bị nghi ngờ (liên quan tới lừa đảo, giao dịch bất thường).',
    '09': 'Thẻ/Tài khoản của khách hàng chưa đăng ký dịch vụ InternetBanking tại ngân hàng.',
    '10': 'Khách hàng xác thực thông tin thẻ/tài khoản không đúng quá 3 lần.',
    '11': 'Đã hết hạn chờ thanh toán. Xin quý khách vui lòng thực hiện lại giao dịch.',
    '12': 'Thẻ/Tài khoản của khách hàng bị khóa.',
    '13': 'Quý khách nhập sai mật khẩu xác thực giao dịch (OTP).',
    '24': 'Khách hàng hủy giao dịch.',
    '51': 'Tài khoản của quý khách không đủ số dư để thực hiện giao dịch.',
    '65': 'Tài khoản của Quý khách đã vượt quá hạn mức giao dịch trong ngày.',
    '75': 'Ngân hàng thanh toán đang bảo trì.',
    '79': 'KH nhập sai mật khẩu thanh toán quá số lần quy định.',
    '99': 'Các lỗi khác (lỗi không xác định).'
}

def get_vnpay_response_message(code):
    return VNPAY_RESPONSE_CODES.get(str(code), 'Giao dịch không hoàn tất hoặc có lỗi phát sinh.')

def build_vnpay_payment_url(order, request_ip, return_url=None):
    load_dotenv(override=True)
    tmn_code = os.getenv('VNPAY_TMN_CODE') or os.getenv('vnp_TmnCode') or VNPAY_TMN_CODE
    hash_secret = os.getenv('VNPAY_HASH_SECRET') or os.getenv('vnp_HashSecret') or VNPAY_HASH_SECRET
    vnpay_url = os.getenv('VNPAY_URL') or os.getenv('vnp_Url') or VNPAY_URL

    if not return_url:
        return_url = os.getenv('VNPAY_RETURN_URL') or os.getenv('vnp_ReturnUrl') or VNPAY_RETURN_URL

    now = datetime.now()
    create_date = now.strftime('%Y%m%d%H%M%S')
    expire_date = (now + timedelta(minutes=15)).strftime('%Y%m%d%H%M%S')

    txn_ref = f"{order.id}_{int(now.timestamp())}"
    amount_in_cents = int(float(order.total_amount) * 100)
    order_info = f"Thanh toan don hang {order.id} tai Food Shoppe"

    params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': tmn_code,
        'vnp_Amount': str(amount_in_cents),
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': txn_ref,
        'vnp_OrderInfo': order_info,
        'vnp_OrderType': 'other',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': request_ip or '127.0.0.1',
        'vnp_CreateDate': create_date,
        'vnp_ExpireDate': expire_date
    }

    sorted_params = sorted(params.items())
    hash_data = '&'.join(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params)
    secure_hash = hmac.new(hash_secret.encode('utf-8'), hash_data.encode('utf-8'), hashlib.sha512).hexdigest()

    return f"{vnpay_url}?{hash_data}&vnp_SecureHash={secure_hash}"

def verify_vnpay_response(query_dict):
    load_dotenv(override=True)
    received_hash = query_dict.get('vnp_SecureHash', '')
    if not received_hash:
        return False

    hash_secret = os.getenv('VNPAY_HASH_SECRET') or os.getenv('vnp_HashSecret') or VNPAY_HASH_SECRET

    filtered_params = {
        k: v for k, v in query_dict.items()
        if k not in ('vnp_SecureHash', 'vnp_SecureHashType')
    }

    sorted_params = sorted(filtered_params.items())
    hash_data = '&'.join(f"{urllib.parse.quote_plus(k)}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params)
    calculated_hash = hmac.new(hash_secret.encode('utf-8'), hash_data.encode('utf-8'), hashlib.sha512).hexdigest()

    return calculated_hash.lower() == received_hash.lower()
