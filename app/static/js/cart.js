function addToCart(restaurantId, dishId, name, price) {
    fetch('/api/carts', {
        method: 'POST',
        body: JSON.stringify({
            "restaurant_id": restaurantId,
            "dish_id": dishId,
            "name": name,
            "price": price
        }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) {
            if (typeof showToast === 'function') {
                showToast("Lỗi: " + data.error);
            } else {
                alert("Lỗi: " + data.error);
            }
            return;
        }

        const totalQty = (data.stats && typeof data.stats.total_quantity !== 'undefined')
            ? data.stats.total_quantity
            : 0;

        let counters = document.querySelectorAll('.cart-counter');
        counters.forEach(c => {
            c.innerText = totalQty;
        });

        const floatingCart = document.getElementById('floatingCartBtn');
        if (floatingCart) {
            floatingCart.classList.remove('cart-bump');
            void floatingCart.offsetWidth; 
            floatingCart.classList.add('cart-bump');
        }

        if (typeof showToast === 'function') {
            showToast(`Đã thêm <b>${name}</b> vào giỏ hàng!`);
        }
    })
    .catch(err => {
        console.error('Lỗi khi thêm vào giỏ hàng:', err);
    });
}

function updateCart(restaurantId, dishId, inputObj) {
    let quantity = parseInt(inputObj.value);

    if (quantity <= 0) {
        deleteCart(restaurantId, dishId);
        return;
    }

    fetch(`/api/carts/${restaurantId}/${dishId}`, {
        method: 'PUT',
        body: JSON.stringify({ 'quantity': quantity }),
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return alert("Lỗi: " + data.error);

        let subtotalEl = document.getElementById(`subtotal-${restaurantId}-${dishId}`);
        if (subtotalEl) subtotalEl.innerText = data.item_subtotal.toLocaleString('vi-VN');

        let resAmountEl = document.getElementById(`res-amount-${restaurantId}`);
        if (resAmountEl) resAmountEl.innerText = data.res_total_amount.toLocaleString('vi-VN');

        document.querySelector('.cart-amount').innerText = data.grand_total_amount.toLocaleString('vi-VN');
        document.querySelectorAll('.cart-counter').forEach(c => c.innerText = data.grand_total_quantity);
    });
}

function deleteCart(restaurantId, dishId) {
    if (!confirm("Bạn chắc chắn muốn xóa món này?")) return;

    fetch(`/api/carts/${restaurantId}/${dishId}`, {
        method: 'DELETE'
    })
    .then(res => res.json())
    .then(data => {
        if (data.error) return alert("Lỗi: " + data.error);

        let itemRow = document.getElementById(`cart-item-${restaurantId}-${dishId}`);
        if (itemRow) itemRow.remove();

        if (data.res_items_left === 0) {
            let resCard = document.getElementById(`cart-res-${restaurantId}`);
            if (resCard) resCard.remove();
        } else {
            let resAmountEl = document.getElementById(`res-amount-${restaurantId}`);
            if (resAmountEl) resAmountEl.innerText = data.res_total_amount.toLocaleString('vi-VN');
        }

        if (data.grand_total_quantity === 0) {
            location.reload();
        } else {
            document.querySelector('.cart-amount').innerText = data.grand_total_amount.toLocaleString('vi-VN');
            document.querySelectorAll('.cart-counter').forEach(c => c.innerText = data.grand_total_quantity);
        }
    });
}

let currentCheckoutRestaurantId = null;

function payRestaurant(restaurantId, restaurantName, totalAmount) {
    currentCheckoutRestaurantId = restaurantId;

    const modal = document.getElementById('checkoutModalBackdrop');
    if (!modal) return;

    const titleEl = document.getElementById('modalResTitle');
    if (titleEl) {
        titleEl.innerText = restaurantName || `Nhà hàng #${restaurantId}`;
    }

    const totalEl = document.getElementById('modalResTotal');
    if (totalEl) {
        totalEl.innerText = (totalAmount || '0') + ' ₫';
    }

    const addrInput = document.getElementById('checkoutAddressInput');
    if (addrInput) {
        const userAddr = (typeof window.DEFAULT_USER_ADDRESS !== 'undefined' && window.DEFAULT_USER_ADDRESS) ? window.DEFAULT_USER_ADDRESS : "";
        addrInput.value = userAddr;
    }

    selectPaymentMethod('CASH');
    modal.style.display = 'flex';
}

function closeCheckoutModal() {
    const modal = document.getElementById('checkoutModalBackdrop');
    if (modal) {
        modal.style.display = 'none';
    }
    currentCheckoutRestaurantId = null;
}

function selectPaymentMethod(method) {
    const cashRadio = document.querySelector('input[name="checkout_payment_method"][value="CASH"]');
    const vnpayRadio = document.querySelector('input[name="checkout_payment_method"][value="VNPAY"]');
    const cardCash = document.getElementById('card-method-CASH');
    const cardVnpay = document.getElementById('card-method-VNPAY');

    if (method === 'VNPAY') {
        if (vnpayRadio) vnpayRadio.checked = true;
        if (cardVnpay) cardVnpay.classList.add('active');
        if (cardCash) cardCash.classList.remove('active');
    } else {
        if (cashRadio) cashRadio.checked = true;
        if (cardCash) cardCash.classList.add('active');
        if (cardVnpay) cardVnpay.classList.remove('active');
    }
}

function submitCheckoutModal() {
    if (!currentCheckoutRestaurantId) return;

    const addrInput = document.getElementById('checkoutAddressInput');
    const address = addrInput ? addrInput.value.trim() : "";

    if (!address) {
        alert("Vui lòng nhập địa chỉ giao hàng của bạn!");
        if (addrInput) addrInput.focus();
        return;
    }

    const selectedRadio = document.querySelector('input[name="checkout_payment_method"]:checked');
    const paymentMethod = selectedRadio ? selectedRadio.value : 'CASH';

    const btn = document.getElementById('btnConfirmCheckout');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang xử lý...';
    }

    fetch(`/api/checkout/${currentCheckoutRestaurantId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            delivery_address: address,
            payment_method: paymentMethod
        })
    })
    .then(res => {
        if (res.status === 401) {
            alert("Vui lòng đăng nhập để đặt hàng!");
            window.location.href = '/login?next=/cart';
            throw new Error('Unauthorized');
        }
        return res.json();
    })
    .then(data => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Xác Nhận Đặt Hàng';
        }

        if (data.error) {
            return alert("Lỗi: " + data.error);
        }

        const resId = currentCheckoutRestaurantId;
        closeCheckoutModal();

        if (resId) {
            const resCard = document.getElementById(`cart-res-${resId}`);
            if (resCard) resCard.remove();
        }

        const remainingCards = document.querySelectorAll('.restaurant-cart-card');
        const emptyMsg = document.getElementById('empty-cart-msg');
        const cartWrapper = document.getElementById('cart-content-wrapper');

        const remainingQty = (data.grand_total_quantity !== undefined) ? data.grand_total_quantity : remainingCards.length;
        const remainingAmt = (data.grand_total_amount !== undefined) ? data.grand_total_amount : 0;

        document.querySelectorAll('.cart-counter').forEach(c => c.innerText = remainingQty);
        const amtEl = document.querySelector('.cart-amount');
        if (amtEl) amtEl.innerText = remainingAmt.toLocaleString('vi-VN');

        if (remainingCards.length === 0 || remainingQty === 0) {
            if (cartWrapper) cartWrapper.style.display = 'none';
            if (emptyMsg) emptyMsg.style.display = 'block';
        }

        if (data.payment_method === 'VNPAY' && data.payment_url) {
            openVNPayModal(data.order_id, data.total_amount, data.payment_url);
            return;
        }

        alert(data.message || `Đặt hàng thành công! Mã đơn hàng: #${data.order_id}`);
    })
    .catch(err => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-check"></i> Xác Nhận Đặt Hàng';
        }
        if (err.message !== 'Unauthorized') {
            console.error('Lỗi thanh toán:', err);
            alert("Đã xảy ra lỗi hệ thống khi đặt hàng.");
        }
    });
}

let currentVNPayOrderId = null;

function switchVNPayTab(tabName) {
    const tabTestCard = document.getElementById('vnpayTabTestCard');
    const tabQr = document.getElementById('vnpayTabQr');
    const btnTestCard = document.getElementById('tabBtnTestCard');
    const btnQr = document.getElementById('tabBtnQr');

    if (!tabTestCard || !tabQr || !btnTestCard || !btnQr) return;

    if (tabName === 'testcard') {
        tabTestCard.style.display = 'block';
        tabQr.style.display = 'none';
        btnTestCard.style.background = '#005cb4';
        btnTestCard.style.color = '#fff';
        btnTestCard.style.border = 'none';
        btnQr.style.background = '#ffffff';
        btnQr.style.color = '#2c4c3b';
        btnQr.style.border = '1.5px solid #ebd9bf';
    } else if (tabName === 'qr') {
        tabTestCard.style.display = 'none';
        tabQr.style.display = 'block';
        btnTestCard.style.background = '#ffffff';
        btnTestCard.style.color = '#2c4c3b';
        btnTestCard.style.border = '1.5px solid #ebd9bf';
        btnQr.style.background = '#005cb4';
        btnQr.style.color = '#fff';
        btnQr.style.border = 'none';
    }
}

function fillTestCardData() {
    const num = document.getElementById('vnpayCardNumber');
    const holder = document.getElementById('vnpayCardHolder');
    const date = document.getElementById('vnpayCardDate');
    const otp = document.getElementById('vnpayCardOtp');
    if (num) num.value = '9704 1985 2619 1432 198';
    if (holder) holder.value = 'NGUYEN VAN A';
    if (date) date.value = '07/15';
    if (otp) otp.value = '123456';
}

function formatCardNumberInput(input) {
    let val = input.value.replace(/\D/g, '');
    let formatted = '';
    for (let i = 0; i < val.length; i++) {
        if (i > 0 && i % 4 === 0) formatted += ' ';
        formatted += val[i];
    }
    input.value = formatted;
}

function formatDateInput(input) {
    let val = input.value.replace(/\D/g, '');
    if (val.length >= 2) {
        input.value = val.slice(0, 2) + '/' + val.slice(2, 4);
    } else {
        input.value = val;
    }
}

function submitBankCardPayment() {
    if (!currentVNPayOrderId) {
        alert("Không tìm thấy thông tin đơn hàng!");
        return;
    }

    const cardNum = (document.getElementById('vnpayCardNumber')?.value || '').replace(/\s+/g, '');
    const cardHolder = (document.getElementById('vnpayCardHolder')?.value || '').trim();
    const cardDate = (document.getElementById('vnpayCardDate')?.value || '').trim();
    const cardOtp = (document.getElementById('vnpayCardOtp')?.value || '').trim();

    if (!cardNum) {
        alert("Vui lòng nhập số thẻ ngân hàng (hoặc nhấn nút 'Điền NGUYEN VAN A')!");
        document.getElementById('vnpayCardNumber')?.focus();
        return;
    }
    if (!cardHolder) {
        alert("Vui lòng nhập tên chủ thẻ (NGUYEN VAN A)!");
        document.getElementById('vnpayCardHolder')?.focus();
        return;
    }
    if (!cardDate) {
        alert("Vui lòng nhập ngày phát hành (07/15)!");
        document.getElementById('vnpayCardDate')?.focus();
        return;
    }
    if (!cardOtp) {
        alert("Vui lòng nhập mã xác thực OTP (123456)!");
        document.getElementById('vnpayCardOtp')?.focus();
        return;
    }

    const btn = document.getElementById('btnPayWithTestCard');
    let origHtml = '';
    if (btn) {
        origHtml = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang xác thực thẻ NGUYEN VAN A...';
    }

    fetch(`/api/orders/${currentVNPayOrderId}/pay_vnpay_test`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            card_number: cardNum,
            card_holder: cardHolder,
            issue_date: cardDate,
            otp: cardOtp
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.status === 'success' && data.redirect_url) {
            window.location.href = data.redirect_url;
        } else {
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = origHtml;
            }
            alert(data.error || data.message || "Xác thực thẻ không thành công!");
        }
    })
    .catch(err => {
        console.error(err);
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = origHtml;
        }
        alert("Đã xảy ra lỗi kết nối khi xác thực thẻ ngân hàng.");
    });
}

function payWithTestCard() {
    submitBankCardPayment();
}

function openVNPayModal(orderId, totalAmount, paymentUrl) {
    currentVNPayOrderId = orderId;
    const modal = document.getElementById('vnpayPaymentModalBackdrop');
    if (!modal) return;

    const subTitle = document.getElementById('vnpayModalOrderSubtitle');
    if (subTitle) subTitle.innerText = `Mã đơn hàng: #${orderId}`;

    const amtEl = document.getElementById('vnpayModalAmount');
    if (amtEl) amtEl.innerText = Number(totalAmount).toLocaleString('vi-VN') + ' ₫';

    const memoEl = document.getElementById('vnpayTransferContent');
    const memo = `DH${orderId}`;
    if (memoEl) memoEl.innerText = memo;

    const qrImg = document.getElementById('vnpayModalQrImg');
    if (qrImg) {
        const qrUrl = `https://img.vietqr.io/image/970428-9704198526191432198-compact2.png?amount=${Math.round(totalAmount)}&addInfo=${encodeURIComponent(memo)}&accountName=${encodeURIComponent('FOOD SHOPPE')}`;
        qrImg.src = qrUrl;
    }

    const gatewayBtn = document.getElementById('btnOpenVnpayGateway');
    if (gatewayBtn) {
        gatewayBtn.href = paymentUrl || '#';
    }

    switchVNPayTab('testcard');

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden';
}

function closeVNPayModal() {
    const modal = document.getElementById('vnpayPaymentModalBackdrop');
    if (modal) modal.style.display = 'none';
    document.body.style.overflow = '';
}

function copyPaymentText(text, btnElement) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        const orig = btnElement.innerHTML;
        btnElement.innerHTML = '<i class="fa-solid fa-check"></i> Đã chép!';
        btnElement.style.background = '#d4edda';
        btnElement.style.color = '#155724';
        setTimeout(() => {
            btnElement.innerHTML = orig;
            btnElement.style.background = '';
            btnElement.style.color = '';
        }, 2000);
    }).catch(() => {
        alert("Đã sao chép: " + text);
    });
}

function confirmPaymentDone() {
    if (!currentVNPayOrderId) {
        closeVNPayModal();
        window.location.href = '/orders';
        return;
    }

    const btn = document.getElementById('btnConfirmPaid');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Đang xác nhận...';
    }

    fetch(`/api/orders/${currentVNPayOrderId}/confirm_payment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
    .then(data => {
        closeVNPayModal();
        alert(data.message || "Xác nhận thanh toán thành công! Đang chuyển đến trang theo dõi đơn hàng.");
        window.location.href = '/orders';
    })
    .catch(err => {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Tôi Đã Chuyển Khoản Xong';
        }
        window.location.href = '/orders';
    });
}

document.addEventListener('click', function (e) {
    const checkoutModal = document.getElementById('checkoutModalBackdrop');
    if (e.target === checkoutModal) {
        closeCheckoutModal();
    }
    const vnpayModal = document.getElementById('vnpayPaymentModalBackdrop');
    if (e.target === vnpayModal) {
        closeVNPayModal();
    }
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeCheckoutModal();
        closeVNPayModal();
    }
});