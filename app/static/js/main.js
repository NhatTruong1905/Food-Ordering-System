// Food Shoppe - Interactive Frontend Logic

document.addEventListener('DOMContentLoaded', () => {
  initModals();
  initOrderSystem();
  initSocialActions();
  initNavScroll();
});

// Toast notification utility
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

// Modal system (Virtual tour, Order, Image preview)
function initModals() {
  const tourModal = document.getElementById('tourModal');
  const orderModal = document.getElementById('orderModal');
  const imageModal = document.getElementById('imageModal');

  // Virtual Tour Triggers
  const tourTriggers = document.querySelectorAll('[data-open-tour]');
  tourTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      if (tourModal) tourModal.classList.add('active');
    });
  });

  // Storefront Image Trigger
  const storefrontTrigger = document.querySelector('[data-open-storefront]');
  if (storefrontTrigger && imageModal) {
    storefrontTrigger.addEventListener('click', () => {
      imageModal.classList.add('active');
    });
  }

  // Close modals on clicking close btn or backdrop
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal || e.target.closest('.modal-close-btn')) {
        modal.classList.remove('active');
      }
    });
  });

  // Close on ESC key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-backdrop.active').forEach(m => m.classList.remove('active'));
    }
  });
}

// Quick Order & Catering Logic
function initOrderSystem() {
  const orderModal = document.getElementById('orderModal');
  const orderItemTitle = document.getElementById('orderItemTitle');
  const orderItemNameInput = document.getElementById('orderItemNameInput');
  const orderForm = document.getElementById('orderForm');

  // Trigger quick order buttons
  document.querySelectorAll('[data-order-item]').forEach(btn => {
    btn.addEventListener('click', () => {
      const itemName = btn.getAttribute('data-order-item');
      const itemPrice = btn.getAttribute('data-order-price') || '';
      
      if (orderItemTitle) orderItemTitle.innerText = `${itemName} (${itemPrice})`;
      if (orderItemNameInput) orderItemNameInput.value = itemName;
      if (orderModal) orderModal.classList.add('active');
    });
  });

  // Handle Form Submit
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
          headers: { 'Content-Type': 'application/json' },
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
        // Fallback offline mock response
        showToast(`Cảm ơn ${payload.name}! Đã đặt món ${payload.item_name} thành công!`);
        orderForm.reset();
        if (orderModal) orderModal.classList.remove('active');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = originalText;
      }
    });
  }
}

// Social Action Buttons
function initSocialActions() {
  // Tweet button
  const tweetBtn = document.getElementById('btnTweet');
  if (tweetBtn) {
    tweetBtn.addEventListener('click', (e) => {
      e.preventDefault();
      const text = encodeURIComponent("Check out Food Shoppe Deli, Market & Catering! Delicious gourmet food and cozy atmosphere.");
      const url = encodeURIComponent(window.location.href);
      window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank', 'width=550,height=420');
    });
  }

  // Share button (Copies link + toast)
  const shareBtn = document.getElementById('btnShare');
  if (shareBtn) {
    shareBtn.addEventListener('click', (e) => {
      e.preventDefault();
      if (navigator.clipboard) {
        navigator.clipboard.writeText(window.location.href).then(() => {
          showToast('Đã sao chép liên kết Food Shoppe vào clipboard!');
        });
      } else {
        showToast('Chia sẻ liên kết: ' + window.location.href);
      }
    });
  }

  // Follow button
  const followBtn = document.getElementById('btnFollow');
  if (followBtn) {
    followBtn.addEventListener('click', (e) => {
      e.preventDefault();
      showToast('Đang mở trang mạng xã hội @FoodShoppe...');
      window.open('https://twitter.com', '_blank');
    });
  }
}

// Navigation & Active state
function initNavScroll() {
  const links = document.querySelectorAll('.nav-link');
  links.forEach(link => {
    link.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId.startsWith('#') && targetId.length > 1) {
        e.preventDefault();
        const targetEl = document.querySelector(targetId);
        if (targetEl) {
          links.forEach(l => l.classList.remove('active'));
          this.classList.add('active');
          targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
      }
    });
  });
}
