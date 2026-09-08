function toggleUserDropdown(event) {
    if (event) {
        event.stopPropagation();
    }
    const menu = document.getElementById('userDropdownMenu');
    const btn = document.getElementById('userDropdownBtn');
    if (!menu) return;

    const isOpen = menu.classList.contains('show');
    if (isOpen) {
        menu.classList.remove('show');
        if (btn) btn.classList.remove('active');
    } else {
        menu.classList.add('show');
        if (btn) btn.classList.add('active');
    }
}

document.addEventListener('click', function (event) {
    const menu = document.getElementById('userDropdownMenu');
    const btn = document.getElementById('userDropdownBtn');
    if (menu && menu.classList.contains('show')) {
        if (!menu.contains(event.target) && (!btn || !btn.contains(event.target))) {
            menu.classList.remove('show');
            if (btn) btn.classList.remove('active');
        }
    }
});

document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        const menu = document.getElementById('userDropdownMenu');
        const btn = document.getElementById('userDropdownBtn');
        if (menu && menu.classList.contains('show')) {
            menu.classList.remove('show');
            if (btn) btn.classList.remove('active');
        }
    }
});
