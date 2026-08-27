
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
        if (data.error) return alert("Lỗi: " + data.error);


        let counters = document.querySelectorAll('.cart-counter');
        counters.forEach(c => c.innerText = data.stats.total_quantity);
        alert("Đã thêm món vào giỏ hàng!");
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
    if (!confirm(`Bạn muốn tiến hành đặt đơn hàng riêng cho Nhà hàng #${restaurantId}?`)) return;

    fetch(`/api/checkout/${restaurantId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(res => res.json())
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
    });
}