from flask import Flask, render_template, request, jsonify
import os

app = Flask(__name__,
            template_folder='templates',
            static_folder='static')

DAILY_SPECIALS = [
    {
        "id": 1,
        "title": "Classic Reuben",
        "description": "House-cured corned beef, Swiss cheese, sauerkraut, Russian dressing on artisan rye.",
        "price": "$12.95",
        "tag": "Popular"
    },
    {
        "id": 2,
        "title": "Smoked Turkey & Brie Panini",
        "description": "Roasted turkey breast, French brie, crisp green apples, honey Dijon on sourdough.",
        "price": "$11.50",
        "tag": "Chef's Pick"
    },
    {
        "id": 3,
        "title": "Artisanal Cheese & Charcuterie Box",
        "description": "Curated selection of local farmstead cheeses, cured meats, olives, and fig jam.",
        "price": "$18.00",
        "tag": "Market Fresh"
    },
    {
        "id": 4,
        "title": "Farmhouse Harvest Salad",
        "description": "Organic mixed greens, goat cheese, roasted walnuts, dried cranberries, balsamic vinaigrette.",
        "price": "$9.75",
        "tag": "Vegetarian"
    }
]

TESTIMONIALS = [
    {
        "name": "Sarah Jenkins",
        "comment": "The best deli in town! Authentic flavors, warm friendly staff, and the Reuben sandwich is unmatched.",
        "rating": 5
    },
    {
        "name": "Mark D.",
        "comment": "Food Shoppe catered our company picnic last week. Everyone raved about the fresh gourmet platters!",
        "rating": 5
    },
    {
        "name": "Emily Watson",
        "comment": "Stepping inside feels like home. Their shelves are packed with the finest local treats and fresh coffee.",
        "rating": 5
    }
]

GALLERY_IMAGES = [
    {"title": "Cozy Front Porch & Storefront", "src": "/static/images/storefront.jpg", "caption": "Welcoming you 7 days a week"},
    {"title": "Artisanal Market Shelves", "src": "/static/images/interior_tour.jpg", "caption": "Handpicked gourmet pantry & cheeses"},
]

@app.route('/')
def home():
    return render_template(
        'index.html',
        specials=DAILY_SPECIALS,
        testimonials=TESTIMONIALS,
        gallery=GALLERY_IMAGES,
        phone="(123) 456-7890",
        email="info@foodshoppe.com",
        address="124 Gourmet Boulevard, Deli District",
        hours="Mon-Sun: 9:00 AM – 7:00 PM"
    )

@app.route('/api/specials')
def get_specials():
    return jsonify({"status": "success", "data": DAILY_SPECIALS})

@app.route('/api/order', methods=['POST'])
def place_order():
    data = request.get_json() or {}
    item_name = data.get('item_name', 'Custom Order')
    customer_name = data.get('name', 'Guest')
    
    return jsonify({
        "status": "success",
        "message": f"Cảm ơn {customer_name}! Yêu cầu đặt món '{item_name}' đã được tiếp nhận thành công.",
        "order_id": "FS-" + str(os.urandom(3).hex()).upper()
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f" * Food Shoppe running on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=True)
