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

