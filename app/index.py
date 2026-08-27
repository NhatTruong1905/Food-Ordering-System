from flask import render_template, request, jsonify
from app import app
from app import dao


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/restaurants', methods=['GET'])
def restaurants():
    try:
        name = request.args.get('name', '').strip()
        address = request.args.get('address', '').strip()
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 6, type=int)

        restaurants_list, total_count, total_pages = dao.get_restaurant(
            name=name if name else None,
            address=address if address else None,
            page=page,
            page_size=page_size
        )

        data = []
        for r in restaurants_list:
            data.append({
                'id': r.id,
                'name': r.name,
                'address': r.address if r.address else None,
                'description': r.description if r.description else None,
                'image_url': r.image_url if r.image_url else None,
                'phone': r.owner.phone if (hasattr(r, 'owner') and r.owner and r.owner.phone) else None,
                'latitude': r.latitude if r.latitude is not None else None,
                'longitude': r.longitude if r.longitude is not None else None,
                'rating_avg': r.rating_avg if (r.rating_avg is not None and r.rating_avg > 0) else None
            })

        return jsonify({
            'status': 'success',
            'restaurants': data,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages
        }), 200

    except Exception as err:
        return jsonify({
            'status': 'error',
            'error': str(err),
        }), 400


@app.route('/api/restaurants/<int:restaurant_id>/dishes', methods=['GET'])
def restaurant_dishes(restaurant_id):
    try:
        restaurant = dao.get_restaurant_by_id(restaurant_id)
        if not restaurant:
            return jsonify({
                'status': 'error',
                'message': 'Nhà hàng không tồn tại'
            }), 404

        dishes_list = dao.get_dishes_by_restaurant(restaurant_id)
        data = []
        for d in dishes_list:
            price_val = float(d.price) if d.price else 0.0
            price_formatted = f"{int(price_val):,} VNĐ".replace(",", ".")
            data.append({
                'id': d.id,
                'restaurant_id': d.restaurant_id,
                'category_name': d.category.name if d.category else 'Món ngon',
                'name': d.name,
                'description': d.description if d.description else None,
                'price': price_val,
                'price_formatted': price_formatted,
                'image_url': d.image_url if d.image_url else None,
                'flavor_tags': d.flavor_tags if d.flavor_tags else None
            })

        return jsonify({
            'status': 'success',
            'restaurant': {
                'id': restaurant.id,
                'name': restaurant.name,
                'address': restaurant.address,
                'rating_avg': restaurant.rating_avg
            },
            'dishes': data,
            'total': len(data)
        }), 200

    except Exception as err:
        return jsonify({
            'status': 'error',
            'error': str(err),
        }), 400
