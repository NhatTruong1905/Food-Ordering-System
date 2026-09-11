document.addEventListener('DOMContentLoaded', () => {
    initModals();
    initOrderSystem();
    initNavScroll();
    initRestaurantSearch();
});

function showToast(message, duration = 3500) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<i class="fa-solid fa-circle-check" style="margin-right:8px; color:#e5be58;"></i> ${message}`;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(10px)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

function initModals() {
    const tourModal = document.getElementById('tourModal');

    const tourTriggers = document.querySelectorAll('[data-open-tour]');
    tourTriggers.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            if (tourModal) tourModal.classList.add('active');
        });
    });

    document.querySelectorAll('.modal-backdrop').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal || e.target.closest('.modal-close-btn') || e.target.closest('.modal-close-btn-inline')) {
                modal.classList.remove('active');
            }
        });
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            document.querySelectorAll('.modal-backdrop.active').forEach(m => m.classList.remove('active'));
        }
    });
}

function initOrderSystem() {
    const orderModal = document.getElementById('orderModal');
    const orderItemTitle = document.getElementById('orderItemTitle');
    const orderItemNameInput = document.getElementById('orderItemNameInput');
    const orderForm = document.getElementById('orderForm');

    document.querySelectorAll('[data-order-item]').forEach(btn => {
        btn.addEventListener('click', () => {
            const itemName = btn.getAttribute('data-order-item');
            const itemPrice = btn.getAttribute('data-order-price') || '';

            if (orderItemTitle) orderItemTitle.innerText = `${itemName} (${itemPrice})`;
            if (orderItemNameInput) orderItemNameInput.value = itemName;
            if (orderModal) orderModal.classList.add('active');
        });
    });

    if (orderForm) {
        orderForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const submitBtn = orderForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerText;
            submitBtn.disabled = true;
            submitBtn.innerText = 'Đang gửi yêu cầu...';

            const payload = {
                name: document.getElementById('custName').value,
                phone: document.getElementById('custPhone').value,
                item_name: orderItemNameInput.value,
                notes: document.getElementById('custNotes').value
            };

            try {
                const res = await fetch('/api/order', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(payload)
                });

                const data = await res.json();
                if (data.status === 'success') {
                    showToast(`Đã nhận đơn hàng #${data.order_id}! Cửa hàng sẽ liên hệ bạn sớm.`);
                    orderForm.reset();
                    if (orderModal) orderModal.classList.remove('active');
                } else {
                    showToast('Có lỗi xảy ra, vui lòng thử lại!');
                }
            } catch (err) {
                showToast(`Cảm ơn ${payload.name}! Đã gửi yêu cầu ${payload.item_name} thành công!`);
                orderForm.reset();
                if (orderModal) orderModal.classList.remove('active');
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerText = originalText;
            }
        });
    }
}

function initNavScroll() {
    const links = document.querySelectorAll('.nav-link');
    links.forEach(link => {
        link.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId && targetId.startsWith('#') && targetId.length > 1) {
                e.preventDefault();
                const targetEl = document.querySelector(targetId);
                if (targetEl) {
                    links.forEach(l => l.classList.remove('active'));
                    this.classList.add('active');
                    targetEl.scrollIntoView({behavior: 'smooth', block: 'start'});
                }
            }
        });
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return String(text)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function openRestaurantDetail(r) {
    const modal = document.getElementById('restaurantDetailModal');
    if (!modal || !r) return;

    const titleEl = document.getElementById('modalResTitle');
    const imgEl = document.getElementById('modalResImg');
    const hoursEl = document.getElementById('modalResHours');
    const hoursRow = document.getElementById('modalResHoursRow');
    const phoneLink = document.getElementById('modalResPhoneLink');
    const phoneRow = document.getElementById('modalResPhoneRow');
    const addressEl = document.getElementById('modalResAddress');
    const addressRow = document.getElementById('modalResAddressRow');
    const descEl = document.getElementById('modalResDesc');
    const descRow = document.getElementById('modalResDescRow');

    const imgUrl = (r.image_url && r.image_url.trim())
        ? r.image_url
        : '/static/images/storefront.jpg';

    if (titleEl) titleEl.innerText = r.name || 'Amazing food & friendly atmosphere';
    if (imgEl) imgEl.src = imgUrl;

    if (hoursRow && hoursEl) {
        hoursRow.style.display = 'flex';
        hoursEl.innerText = '9:00 AM – 10:00 PM (Thứ 2 – Chủ Nhật)';
    }

    if (phoneRow && phoneLink) {
        const phoneVal = r.phone || '(028) 3822 9999';
        phoneLink.href = `tel:${phoneVal}`;
        phoneLink.innerText = phoneVal;
        phoneRow.style.display = 'flex';
    }

    if (addressRow && addressEl) {
        if (r.address && r.address.trim()) {
            addressEl.innerText = r.address;
            addressRow.style.display = 'flex';
        } else {
            addressRow.style.display = 'none';
        }
    }

    if (descRow && descEl) {
        if (r.description && r.description.trim()) {
            descEl.innerText = r.description;
            descRow.style.display = 'flex';
        } else {
            descRow.style.display = 'none';
        }
    }

    modal.classList.add('active');
}

async function fetchAndDisplayDishes(restaurantId, restaurantName, doScroll = true) {
    const titleEl = document.getElementById('activeMenuRestaurantTitle');
    const subEl = document.getElementById('activeMenuRestaurantSub');
    const countBadge = document.getElementById('activeMenuDishCount');
    const countText = document.getElementById('dishCountText');
    const grid = document.getElementById('dishesGrid');
    const noDishesBox = document.getElementById('noDishesFound');
    const dishesSection = document.getElementById('restaurantDishes');

    if (titleEl && restaurantName) {
        titleEl.innerHTML = `<i class="fa-solid fa-utensils" style="color: var(--accent-gold); margin-right: 8px;"></i> Thực Đơn: ${escapeHtml(restaurantName)}`;
    }
    if (subEl) {
        subEl.innerText = `Khám phá các món ăn đặc sắc và tươi ngon được chế biến theo phong cách riêng của quán`;
    }

    try {
        const res = await fetch(`/api/restaurants/${restaurantId}/dishes`);
        const data = await res.json();

        if (data.dishes && data.dishes.length > 0) {
            if (countBadge && countText) {
                countText.innerText = `${data.total} món`;
                countBadge.style.display = 'inline-flex';
            }
            if (noDishesBox) noDishesBox.style.display = 'none';

            if (grid) {
                grid.innerHTML = data.dishes.map(d => {
                    const imgHtml = d.image_url
                        ? `<div style="width: 70px; height: 70px; flex-shrink:0; border-radius:6px; overflow:hidden; border:1px solid #e0d5c1;">
                <img src="${d.image_url}" alt="${escapeHtml(d.name)}" style="width:100%; height:100%; object-fit:cover; display:block;">
               </div>`
                        : '';

                    const descHtml = d.description
                        ? `<p class="special-desc" style="margin-top:4px;">${escapeHtml(d.description)}</p>`
                        : '';

                    const ratingHtml = (d.rating_avg && Number(d.rating_avg) > 0)
                        ? `<div style="margin-top:5px;">
                            <span class="dish-rating-badge" onclick="openDishReviewsModal(${d.id})" style="cursor: pointer; font-size: 11.5px; font-weight: 700; color: #b8860b; background: #fff8e7; border: 1px solid #ebd9bf; padding: 2px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 4px;" title="Xem các nhận xét">
                              <i class="fa-solid fa-star" style="color: #f1c40f;"></i> ${Number(d.rating_avg).toFixed(1)} <span style="font-weight: 500; color: #777;">(${d.review_count})</span>
                            </span>
                           </div>`
                        : '';

                    const flavorHtml = d.flavor_tags
                        ? `<div style="margin-top:6px; font-size:11px; color:#786951;"><i class="fa-solid fa-tag"></i> ${escapeHtml(d.flavor_tags)}</div>`
                        : '';

                    return `
            <div class="special-item-card">
              <div style="display:flex; gap:12px; align-items:flex-start;">
                ${imgHtml}
                <div style="flex:1;">
                  <div class="special-header">
                    <h3 class="special-title">${escapeHtml(d.name)}</h3>
                    <span class="special-price">${d.price_formatted}</span>
                  </div>
                  ${ratingHtml}
                  ${descHtml}
                  ${flavorHtml}
                </div>
              </div>
              <div class="special-footer" style="margin-top:10px;">
                <span class="special-badge">${escapeHtml(d.category_name || 'Món ngon')}</span>
                <button type="button" class="btn-order-quick"
                        data-res-id="${restaurantId}"
                        data-dish-id="${d.id}"
                        data-name="${escapeHtml(d.name)}"
                        data-price="${d.price}">
                  <i class="fa-solid fa-cart-plus"></i> Đặt món
                </button>
              </div>
            </div>
          `;
                }).join('');

                grid.querySelectorAll('.btn-order-quick').forEach(btn => {
                    btn.addEventListener('click', async (e) => {
                        e.preventDefault();

                        const resId = btn.getAttribute('data-res-id');
                        const dishId = btn.getAttribute('data-dish-id');
                        const name = btn.getAttribute('data-name');
                        const price = parseFloat(btn.getAttribute('data-price'));

                        addToCart(resId, dishId, name, price);

                        const originalHtml = btn.innerHTML;
                        btn.innerHTML = `<i class="fa-solid fa-check"></i> Đã thêm`;
                        btn.style.backgroundColor = 'var(--primary-green-dark)';
                        btn.style.color = 'white';

                        setTimeout(() => {
                            btn.innerHTML = originalHtml;
                            btn.style.backgroundColor = '';
                            btn.style.color = '';
                        }, 1500);
                    });
                });
            }
        } else {
            if (grid) grid.innerHTML = '';
            if (countBadge) countBadge.style.display = 'none';
            if (noDishesBox) noDishesBox.style.display = 'block';
        }

        if (doScroll && dishesSection) {
            dishesSection.scrollIntoView({behavior: 'smooth', block: 'start'});
        }
    } catch (err) {
        console.error('Lỗi khi tải món ăn nhà hàng:', err);
    }
}

async function fetchAndDisplayRestaurantReviews(restaurantId, restaurantName) {
    const section = document.getElementById('testimonials');
    const grid = document.getElementById('testimonialGrid');
    const badge = document.getElementById('testimonialsRestaurantBadge');
    const emptyMsg = document.getElementById('noTestimonialsMsg');

    if (!section || !grid) return;

    section.style.display = 'block';

    if (badge && restaurantName) {
        badge.innerHTML = `<i class="fa-solid fa-store" style="color:#b8860b;"></i> ${escapeHtml(restaurantName)}`;
        badge.style.display = 'inline-block';
    }

    try {
        const res = await fetch(`/api/restaurants/${restaurantId}/reviews`);
        const data = await res.json();

        if (data.status === 'success' && data.reviews && data.reviews.length > 0) {
            if (emptyMsg) emptyMsg.style.display = 'none';
            grid.style.display = 'grid';

            grid.innerHTML = data.reviews.map(r => {
                let starsHtml = '';
                for (let i = 0; i < r.rating; i++) {
                    starsHtml += '<i class="fa-solid fa-star"></i>';
                }
                for (let i = r.rating; i < 5; i++) {
                    starsHtml += '<i class="fa-regular fa-star" style="color: #d8cbb8;"></i>';
                }

                const dishBadge = r.dish_name
                    ? `<div style="font-size: 11.5px; font-weight: 700; color: #1a4224; background: #e8f5e9; border: 1px solid #c8e6c9; padding: 2px 8px; border-radius: 4px; display: inline-flex; align-items: center; gap: 4px; margin-bottom: 8px;">
                         <i class="fa-solid fa-utensils"></i> ${escapeHtml(r.dish_name)}
                       </div>`
                    : '';

                const commentText = (r.comment && r.comment.trim())
                    ? `"${escapeHtml(r.comment)}"`
                    : `<em style="color:#888;">(Khách hàng đánh giá ${r.rating} sao)</em>`;

                const dateText = r.created_at ? `<span style="font-weight: 400; font-size: 11px; color: #888;">${r.created_at}</span>` : '';

                return `
                    <div class="testimonial-card" style="box-shadow: 0 2px 8px rgba(0,0,0,0.04); transition: transform 0.2s;" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                        ${dishBadge}
                        <div class="stars" style="color: #f1c40f; margin-bottom: 6px;">
                            ${starsHtml}
                        </div>
                        <p class="quote" style="font-style: italic; color: #333; margin: 4px 0 10px 0; line-height: 1.45;">${commentText}</p>
                        <div class="author" style="display: flex; align-items: center; justify-content: space-between; border-top: 1px dotted #ebd9bf; padding-top: 6px;">
                            <span>— ${escapeHtml(r.user_name)}</span>
                            ${dateText}
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            grid.innerHTML = '';
            grid.style.display = 'none';
            if (emptyMsg) emptyMsg.style.display = 'block';
        }
    } catch (err) {
        console.error('Lỗi khi tải nhận xét nhà hàng:', err);
        grid.innerHTML = '';
        grid.style.display = 'none';
        if (emptyMsg) emptyMsg.style.display = 'block';
    }
}

function initRestaurantSearch() {
    const searchInput = document.getElementById('restaurantSearchInput');
    const clearBtn = document.getElementById('btnClearSearch');
    const filterPills = document.querySelectorAll('.filter-pill');
    const grid = document.getElementById('restaurantsGrid');
    const noResultsBox = document.getElementById('noRestaurantsFound');
    const paginationContainer = document.getElementById('restaurantPagination');

    if (!searchInput || !grid) return;

    let currentPage = 1;
    const pageSize = 6;
    let currentSearchQuery = '';
    let currentRestaurants = [];
    let debounceTimer = null;
    let hasInitialDishesLoaded = false;

    function renderRestaurantCards(restaurants) {
        currentRestaurants = restaurants || [];

        if (!restaurants || restaurants.length === 0) {
            grid.innerHTML = '';
            if (noResultsBox) noResultsBox.style.display = 'block';
            return;
        }

        if (noResultsBox) noResultsBox.style.display = 'none';

        grid.innerHTML = restaurants.map((r, index) => {
            const imgUrl = (r.image_url && r.image_url.trim())
                ? r.image_url
                : '/static/images/storefront.jpg';

            const ratingHtml = (r.rating_avg && Number(r.rating_avg) > 0)
                ? `<span class="restaurant-rating-badge"><i class="fa-solid fa-star"></i> ${Number(r.rating_avg).toFixed(1)}</span>`
                : '';

            const addressHtml = (r.address && r.address.trim())
                ? `<p class="restaurant-address"><i class="fa-solid fa-location-dot"></i> ${escapeHtml(r.address)}</p>`
                : '';

            const descHtml = (r.description && r.description.trim())
                ? `<p class="restaurant-desc">${escapeHtml(r.description)}</p>`
                : '';

            return `
        <div class="restaurant-card">
          <div class="restaurant-card-img-wrap btn-trigger-detail" data-res-index="${index}" title="Bấm vào ảnh để xem chi tiết nhà hàng" style="cursor: pointer;">
            <img src="${imgUrl}" alt="${escapeHtml(r.name)}" class="restaurant-card-img">
            <span class="restaurant-status-badge open"><i class="fa-solid fa-circle"></i> Đang mở cửa</span>
            ${ratingHtml}
          </div>
          <div class="restaurant-card-body">
            <h3 class="restaurant-name">${escapeHtml(r.name)}</h3>
            ${addressHtml}
            ${descHtml}
          </div>
          <div class="restaurant-card-footer">
            <button type="button" class="btn-view-restaurant-menu btn-trigger-dishes" data-res-id="${r.id}" data-res-name="${escapeHtml(r.name)}" style="margin-left: auto; border:none; cursor:pointer;">
              <i class="fa-solid fa-utensils"></i> Xem Thực Đơn
            </button>
          </div>
        </div>
      `;
        }).join('');

        grid.querySelectorAll('.btn-trigger-detail').forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const index = parseInt(trigger.getAttribute('data-res-index'), 10);
                if (currentRestaurants[index]) {
                    openRestaurantDetail(currentRestaurants[index]);
                }
            });
        });

        grid.querySelectorAll('.btn-trigger-dishes').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const resId = parseInt(btn.getAttribute('data-res-id'), 10);
                const resName = btn.getAttribute('data-res-name');
                if (resId) {
                    fetchAndDisplayDishes(resId, resName, true);
                    fetchAndDisplayRestaurantReviews(resId, resName);
                }
            });
        });

        grid.querySelectorAll('.restaurant-card-body').forEach(body => {
            body.style.cursor = 'pointer';
            body.title = 'Nhấn để xem thực đơn & nhận xét của nhà hàng';
            body.addEventListener('click', (e) => {
                const card = body.closest('.restaurant-card');
                const btn = card ? card.querySelector('.btn-trigger-dishes') : null;
                if (btn) {
                    const resId = parseInt(btn.getAttribute('data-res-id'), 10);
                    const resName = btn.getAttribute('data-res-name');
                    if (resId) {
                        fetchAndDisplayDishes(resId, resName, true);
                        fetchAndDisplayRestaurantReviews(resId, resName);
                    }
                }
            });
        });

        if (!hasInitialDishesLoaded && currentRestaurants.length > 0) {
            hasInitialDishesLoaded = true;
            fetchAndDisplayDishes(currentRestaurants[0].id, currentRestaurants[0].name, false);
        }
    }

    function renderPagination(total, page, totalPages) {
        if (!paginationContainer) return;

        if (totalPages <= 1 || total <= pageSize) {
            paginationContainer.innerHTML = '';
            paginationContainer.style.display = 'none';
            return;
        }

        paginationContainer.style.display = 'flex';

        let html = '';

        const prevDisabled = page <= 1 ? 'disabled' : '';
        html += `<button type="button" class="pagination-btn" data-page="${page - 1}" ${prevDisabled}>
      <i class="fa-solid fa-chevron-left"></i> Trước
    </button>`;

        for (let i = 1; i <= totalPages; i++) {
            const activeClass = i === page ? 'active' : '';
            html += `<button type="button" class="pagination-btn ${activeClass}" data-page="${i}">${i}</button>`;
        }

        const nextDisabled = page >= totalPages ? 'disabled' : '';
        html += `<button type="button" class="pagination-btn" data-page="${page + 1}" ${nextDisabled}>
      Sau <i class="fa-solid fa-chevron-right"></i>
    </button>`;

        paginationContainer.innerHTML = html;

        paginationContainer.querySelectorAll('.pagination-btn:not(:disabled)').forEach(btn => {
            btn.addEventListener('click', () => {
                const targetPage = parseInt(btn.getAttribute('data-page'), 10);
                if (targetPage && targetPage !== currentPage) {
                    currentPage = targetPage;
                    fetchRestaurants(currentSearchQuery, currentPage);
                    const restaurantsSection = document.getElementById('restaurants');
                    if (restaurantsSection) {
                        restaurantsSection.scrollIntoView({behavior: 'smooth', block: 'start'});
                    }
                }
            });
        });
    }

    async function fetchRestaurants(query = '', page = 1) {
        try {
            const params = new URLSearchParams({
                page: page,
                page_size: pageSize
            });
            if (query) {
                params.append('name', query);
            }

            const res = await fetch(`/api/restaurants?${params.toString()}`);
            const data = await res.json();

            if (data.restaurants) {
                renderRestaurantCards(data.restaurants);
                renderPagination(data.total || 0, data.page || 1, data.total_pages || 1);
            }
        } catch (err) {
            console.error('Lỗi khi tải danh sách nhà hàng:', err);
        }
    }

    fetchRestaurants('', 1);

    searchInput.addEventListener('input', () => {
        currentSearchQuery = searchInput.value.trim();
        if (clearBtn) {
            clearBtn.style.display = currentSearchQuery.length > 0 ? 'flex' : 'none';
        }

        currentPage = 1;
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            fetchRestaurants(currentSearchQuery, 1);
        }, 200);
    });

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            currentSearchQuery = '';
            clearBtn.style.display = 'none';
            filterPills.forEach(p => p.classList.remove('active'));
            const allPill = document.querySelector('.filter-pill[data-filter="all"]');
            if (allPill) allPill.classList.add('active');
            currentPage = 1;
            fetchRestaurants('', 1);
            searchInput.focus();
        });
    }

    filterPills.forEach(pill => {
        pill.addEventListener('click', function () {
            filterPills.forEach(p => p.classList.remove('active'));
            this.classList.add('active');
            const filterVal = this.getAttribute('data-filter') || 'all';

            currentPage = 1;
            if (filterVal === 'all') {
                searchInput.value = '';
                currentSearchQuery = '';
                if (clearBtn) clearBtn.style.display = 'none';
                fetchRestaurants('', 1);
            } else {
                searchInput.value = filterVal;
                currentSearchQuery = filterVal;
                if (clearBtn) clearBtn.style.display = 'flex';
                fetchRestaurants(filterVal, 1);
            }
        });
    });
}

async function openDishReviewsModal(dishId) {
    let modal = document.getElementById('dishReviewsDisplayModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'dishReviewsDisplayModal';
        modal.className = 'checkout-modal-backdrop';
        modal.style.cssText = 'display: none; z-index: 100001; position: fixed; inset: 0; background: rgba(0,0,0,0.6); backdrop-filter: blur(4px); align-items: center; justify-content: center; padding: 16px;';
        modal.innerHTML = `
            <div class="checkout-modal-dialog" style="max-width: 520px; width: 100%; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 20px 50px rgba(0,0,0,0.25); border: 2px solid #ecd8ba; max-height: 85vh; display: flex; flex-direction: column;">
                <div class="checkout-modal-header" style="background: linear-gradient(135deg, #1a4224, #2c4c3b); color: #fff; padding: 16px 20px; display: flex; justify-content: space-between; align-items: center; flex-shrink: 0;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <div style="width: 36px; height: 36px; border-radius: 50%; background: rgba(205,164,52,0.2); color: #f1c40f; display: flex; align-items: center; justify-content: center; font-size: 17px;">
                            <i class="fa-solid fa-star"></i>
                        </div>
                        <div>
                            <h3 id="dishReviewDisplayTitle" style="margin: 0; font-family: 'Playfair Display', Georgia, serif; font-size: 18px; color: #fff;">Đánh Giá Món Ăn</h3>
                            <div id="dishReviewDisplaySub" style="font-size: 12px; color: rgba(255,255,255,0.85); margin-top: 2px;">0 đánh giá</div>
                        </div>
                    </div>
                    <button type="button" onclick="closeDishReviewsModal()" style="color: #fff; background: rgba(255,255,255,0.15); border: none; border-radius: 50%; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; cursor: pointer;">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
                <div id="dishReviewsDisplayList" style="padding: 20px; overflow-y: auto; flex: 1; display: flex; flex-direction: column; gap: 12px;">
                    <div style="text-align: center; color: #777; padding: 20px;">Đang tải đánh giá...</div>
                </div>
                <div style="padding: 12px 20px; background: #faf8f4; border-top: 1px solid #ebd9bf; display: flex; justify-content: flex-end; flex-shrink: 0;">
                    <button type="button" onclick="closeDishReviewsModal()" style="padding: 8px 18px; border: 1.5px solid #ebd9bf; background: #fff; color: #555; border-radius: 6px; font-size: 13px; font-weight: 700; cursor: pointer;">
                        Đóng
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        modal.addEventListener('click', (e) => {
            if (e.target === modal) closeDishReviewsModal();
        });
    }

    modal.style.display = 'flex';
    const listEl = document.getElementById('dishReviewsDisplayList');
    listEl.innerHTML = '<div style="text-align: center; color: #777; padding: 30px;"><i class="fa-solid fa-spinner fa-spin" style="font-size: 24px; color: #cda434;"></i><div style="margin-top: 8px;">Đang tải nhận xét...</div></div>';

    try {
        const res = await fetch(`/api/dishes/${dishId}/reviews`);
        const data = await res.json();
        if (data.status === 'success') {
            document.getElementById('dishReviewDisplayTitle').innerText = data.dish.name;
            document.getElementById('dishReviewDisplaySub').innerText = `${Number(data.dish.rating_avg).toFixed(1)} ★ (${data.total} lượt đánh giá)`;

            if (data.reviews && data.reviews.length > 0) {
                listEl.innerHTML = data.reviews.map(r => `
                    <div style="background: #faf8f4; border: 1px solid #ebd9bf; border-radius: 10px; padding: 12px 16px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                            <span style="font-weight: 700; font-size: 13.5px; color: #1a4224;">
                                <i class="fa-solid fa-user-circle" style="color: #cda434; margin-right: 4px;"></i> ${escapeHtml(r.author_name)}
                            </span>
                            <span style="font-size: 11.5px; color: #888;">${escapeHtml(r.created_at)}</span>
                        </div>
                        <div style="color: #f39c12; font-size: 13px; margin-bottom: 6px;">
                            ${'★'.repeat(r.rating)}${'☆'.repeat(5 - r.rating)}
                        </div>
                        <div style="font-size: 13px; color: #333; line-height: 1.5;">
                            ${r.comment ? escapeHtml(r.comment) : '<span style="color: #888; font-style: italic;">Không có lời bình luận</span>'}
                        </div>
                    </div>
                `).join('');
            } else {
                listEl.innerHTML = '<div style="text-align: center; color: #777; padding: 40px 20px;"><i class="fa-regular fa-comment-dots" style="font-size: 36px; color: #d0c8b8; margin-bottom: 10px;"></i><div>Chưa có đánh giá nào cho món ăn này. Hãy đặt món và trải nghiệm nhé!</div></div>';
            }
        } else {
            listEl.innerHTML = `<div style="color: red; text-align: center; padding: 20px;">${escapeHtml(data.message || 'Lỗi khi tải đánh giá')}</div>`;
        }
    } catch (e) {
        listEl.innerHTML = '<div style="color: red; text-align: center; padding: 20px;">Lỗi kết nối khi tải đánh giá món ăn!</div>';
    }
}

function closeDishReviewsModal() {
    const modal = document.getElementById('dishReviewsDisplayModal');
    if (modal) modal.style.display = 'none';
}

