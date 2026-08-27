def get_cart_stats(cart):
    total_quantity = 0
    total_amount = 0
    if cart:
        for res_data in cart.values():
            for item in res_data.get('items', {}).values():
                total_quantity += item['quantity']
                total_amount += item['quantity'] * item['price']
    return {"total_quantity": total_quantity, "total_amount": total_amount}

def get_res_total(cart, restaurant_id):
    total = 0
    if restaurant_id in cart:
        for item in cart[restaurant_id].get('items', {}).values():
            total += item['quantity'] * item['price']
    return total