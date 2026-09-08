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

function payRestaurant(restaurantId) {
    const address = prompt("Vui lòng nhập địa chỉ giao hàng của bạn (Số nhà, Đường, Quận...):", "");
    if (address === null) return; // Bấm Cancel
    
    if (address.trim() === "") {
        alert("Bạn phải nhập địa chỉ giao hàng để tiếp tục!");
        return;
    }

    if (!confirm(`Xác nhận đặt đơn hàng cho Nhà hàng #${restaurantId} (Thanh toán tiền mặt - COD)?`)) return;

    fetch(`/api/checkout/${restaurantId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            delivery_address: address,
            payment_method: 'CASH'
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
        if (data.error) return alert("Lỗi: " + data.error);

        alert(data.message);

        let resCard = document.getElementById(`cart-res-${restaurantId}`);
        if (resCard) resCard.remove();

        if (data.grand_total_quantity === 0) {
            location.reload();
        } else {
            document.querySelector('.cart-amount').innerText = data.grand_total_amount.toLocaleString('vi-VN');
            document.querySelectorAll('.cart-counter').forEach(c => c.innerText = data.grand_total_quantity);
        }
    })
    .catch(err => {
        if(err.message !== 'Unauthorized') {
            console.error('Lỗi thanh toán:', err);
            alert("Đã xảy ra lỗi hệ thống khi đặt hàng.");
        }
    });
}