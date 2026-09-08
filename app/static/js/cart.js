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

        closeCheckoutModal();

        if (paymentMethod === 'VNPAY') {
            alert(`[VNPAY] Đặt hàng thành công! Mã đơn hàng: #${data.order_id}\nPhương thức thanh toán: Cổng VNPAY`);
        } else {
            alert(data.message || `Đặt hàng thành công! Mã đơn hàng: #${data.order_id}`);
        }

        const resId = currentCheckoutRestaurantId;
        const resCard = document.getElementById(`cart-res-${resId}`);
        if (resCard) resCard.remove();

        if (data.grand_total_quantity === 0) {
            location.reload();
        } else {
            const amtEl = document.querySelector('.cart-amount');
            if (amtEl) amtEl.innerText = data.grand_total_amount.toLocaleString('vi-VN');
            document.querySelectorAll('.cart-counter').forEach(c => c.innerText = data.grand_total_quantity);
        }
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

document.addEventListener('click', function (e) {
    const modalBackdrop = document.getElementById('checkoutModalBackdrop');
    if (e.target === modalBackdrop) {
        closeCheckoutModal();
    }
});

document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        closeCheckoutModal();
    }
});