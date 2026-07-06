/* ============================================================
   CardeTrade — Premium UI/UX JavaScript v2.0
   Micro-interactions, Parallax, Animations
   ============================================================ */

document.addEventListener('DOMContentLoaded', function() {

    'use strict';

    // ==========================================================
    // 1. PRELOADER
    // ==========================================================
    const preloader = document.getElementById('preloader');
    if (preloader) {
        window.addEventListener('load', function() {
            setTimeout(function() { preloader.classList.add('hidden'); }, 400);
        });
        setTimeout(function() { preloader.classList.add('hidden'); }, 1800);
    }

    // ==========================================================
    // 2. NAVBAR SCROLL EFFECT
    // ==========================================================
    const navbar = document.querySelector('.navbar-premium');
    if (navbar) {
        window.addEventListener('scroll', function() {
            navbar.classList.toggle('scrolled', window.scrollY > 80);
        }, { passive: true });
    }

    // ==========================================================
    // 3. SCROLL ANIMATIONS (IntersectionObserver)
    // ==========================================================
    function setupScrollAnimations(selector, className) {
        const els = document.querySelectorAll(selector);
        if (!els.length) return;
        const obs = new IntersectionObserver(function(entries) {
            entries.forEach(function(e) {
                if (e.isIntersecting) { e.target.classList.add(className || 'visible'); }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });
        els.forEach(function(el) { obs.observe(el); });
    }
    setupScrollAnimations('.animate-on-scroll');
    setupScrollAnimations('.animate-on-scroll-left');
    setupScrollAnimations('.animate-on-scroll-right');
    setupScrollAnimations('.animate-on-scroll-scale');

    // ==========================================================
    // 4. COUNTER ANIMATION
    // ==========================================================
    const counters = document.querySelectorAll('.stat-number, .counter-value');
    counters.forEach(function(el) {
        const target = parseInt(el.getAttribute('data-target') || el.textContent.replace(/[^0-9]/g, '')) || 0;
        if (target === 0) { el.textContent = '0'; return; }
        const duration = 1800, steps = 40;
        const stepVal = target / steps;
        let current = 0;
        const obs = new IntersectionObserver(function(entries) {
            if (!entries[0].isIntersecting) return;
            const interval = setInterval(function() {
                current += stepVal;
                if (current >= target) { current = target; clearInterval(interval); }
                el.textContent = Math.round(current);
            }, duration / steps);
            obs.unobserve(el);
        }, { threshold: 0.3 });
        obs.observe(el);
    });

    // ==========================================================
    // 5. ALERTS AUTO-DISMISS
    // ==========================================================
    document.querySelectorAll('.alert-dismissible').forEach(function(a) {
        setTimeout(function() {
            try { bootstrap.Alert.getOrCreateInstance(a).close(); } catch(e) {}
        }, 5000);
    });

    // ==========================================================
    // 6. CARD HOVER TILT EFFECT (3D)
    // ==========================================================
    document.querySelectorAll('.card-premium, .listing-card-premium, .feature-card-premium').forEach(function(card) {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left, y = e.clientY - rect.top;
            const cx = rect.width / 2, cy = rect.height / 2;
            const rx = (y - cy) / 18, ry = (cx - x) / 18;
            card.style.transform = 'perspective(1000px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateY(-4px)';
        });
        card.addEventListener('mouseleave', function() {
            card.style.transform = '';
        });
    });

    // ==========================================================
    // 7. PARALLAX ON HERO IMAGE
    // ==========================================================
    const heroImg = document.querySelector('.hero-overlay img');
    if (heroImg) {
        window.addEventListener('scroll', function() {
            const sy = window.scrollY;
            if (sy < window.innerHeight) {
                heroImg.style.transform = 'translateY(' + (sy * 0.12) + 'px) scale(1.08)';
            }
        }, { passive: true });
    }

    // ==========================================================
    // 8. HERO PARTICLE GENERATOR
    // ==========================================================
    const particleContainer = document.querySelector('.hero-particles');
    if (particleContainer && particleContainer.children.length === 0) {
        for (let i = 0; i < 20; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            p.style.cssText = [
                'top:' + (Math.random() * 100) + '%;',
                'left:' + (Math.random() * 100) + '%;',
                'width:' + (Math.random() * 5 + 2) + 'px;',
                'height:' + p.style.width + ';',
                'animation-delay:' + (Math.random() * 6) + 's;',
                'animation-duration:' + (Math.random() * 5 + 4) + 's;',
                'opacity:' + (Math.random() * 0.3 + 0.08) + ';'
            ].join('');
            particleContainer.appendChild(p);
        }
    }

    // ==========================================================
    // 9. ACTIVE NAV LINK
    // ==========================================================
    const path = window.location.pathname;
    document.querySelectorAll('.navbar-premium .nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && href !== '/' && path.startsWith(href)) link.classList.add('active');
        else if (href === '/' && path === '/') link.classList.add('active');
    });

    // ==========================================================
    // 10. QUANTITY CALCULATOR (Direct Buy)
    // ==========================================================
    document.querySelectorAll('input[name="quantity_kg"]').forEach(function(input) {
        input.addEventListener('input', function() {
            const form = this.closest('form');
            const priceEl = form ? form.querySelector('[data-price]') : null;
            if (!priceEl) return;
            const ppkg = parseFloat(priceEl.dataset.price) || 0;
            const qty = parseFloat(this.value) || 0;
            const total = document.getElementById('totalDisplay');
            const qtyD = document.getElementById('qtyDisplay');
            if (total) total.textContent = 'Rs ' + (ppkg * qty).toFixed(2);
            if (qtyD) qtyD.textContent = qty;
        });
    });

    // ==========================================================
    // 11. TOOLTIPS
    // ==========================================================
    try {
        var tt = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tt.map(function(el) { return new bootstrap.Tooltip(el); });
    } catch(e) {}

    // ==========================================================
    // 12. CONFETTI CELEBRATION (for success messages)
    // ==========================================================
    const confettiBtn = document.getElementById('celebrateBtn');
    if (confettiBtn) {
        confettiBtn.addEventListener('click', function() {
            const colors = ['#c8a951', '#d4af37', '#1a4d2e', '#e8d48b', '#fff'];
            for (let i = 0; i < 60; i++) {
                const piece = document.createElement('div');
                piece.style.cssText = [
                    'position:fixed;z-index:99999;',
                    'width:' + (Math.random() * 8 + 4) + 'px;',
                    'height:' + (Math.random() * 8 + 4) + 'px;',
                    'background:' + colors[Math.floor(Math.random() * colors.length)] + ';',
                    'border-radius:' + (Math.random() > 0.5 ? '50%' : '2px') + ';',
                    'left:' + (Math.random() * 100) + 'vw;',
                    'top:-20px;',
                    'animation:confettiFall ' + (Math.random() * 2 + 2) + 's linear forwards;',
                    'animation-delay:' + (Math.random() * 0.5) + 's;'
                ].join('');
                document.body.appendChild(piece);
                setTimeout(function() { piece.remove(); }, 4000);
            }
        });
    }

    // ==========================================================
    // 13. SCROLL PROGRESS INDICATOR (on hero pages)
    // ==========================================================
    const scrollProgress = document.createElement('div');
    scrollProgress.style.cssText = 'position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--gold));z-index:99999;transition:width 0.1s;';
    document.body.appendChild(scrollProgress);
    window.addEventListener('scroll', function() {
        const h = document.documentElement;
        const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
        scrollProgress.style.width = pct + '%';
    }, { passive: true });

    // ==========================================================
    // 14. RIPPLE EFFECT ON BUTTONS
    // ==========================================================
    document.querySelectorAll('.btn-premium').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            ripple.style.cssText = [
                'position:absolute;border-radius:50%;',
                'width:' + size + 'px;height:' + size + 'px;',
                'left:' + (e.clientX - rect.left - size/2) + 'px;',
                'top:' + (e.clientY - rect.top - size/2) + 'px;',
                'background:rgba(255,255,255,0.3);',
                'animation:rippleEffect 0.6s ease-out forwards;',
                'pointer-events:none;'
            ].join('');
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            setTimeout(function() { ripple.remove(); }, 700);
        });
    });

    // ==========================================================
    // 15. SMOOTH SCROLL FOR ANCHOR LINKS
    // ==========================================================
    document.querySelectorAll('a[href^="#"]').forEach(function(a) {
        a.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ==========================================================
    // 16. TABLE ROW HOVER HIGHLIGHT
    // ==========================================================
    document.querySelectorAll('.table-premium tbody tr').forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.005)';
            this.style.boxShadow = '0 4px 16px rgba(0,0,0,0.04)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.transform = '';
            this.style.boxShadow = '';
        });
    });

    // ==========================================================
    // 17. NOTIFICATION BELL PULSE
    // ==========================================================
    const notifBell = document.getElementById('notifBell');
    if (notifBell) {
        const notifCount = notifBell.querySelector('.notif-count');
        if (notifCount && parseInt(notifCount.textContent) > 0) {
            setInterval(function() {
                notifBell.style.animation = 'heartbeat 1.5s ease-in-out';
                setTimeout(function() { notifBell.style.animation = ''; }, 1500);
            }, 5000);
        }
    }

    // ==========================================================
    // 18. CHAT AUTO-SCROLL TO BOTTOM
    // ==========================================================
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }

    // ==========================================================
    // 19. NAVBAR TOGGLE ANIMATION
    // ==========================================================
    const navbarToggler = document.querySelector('.navbar-premium .navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            this.classList.toggle('collapsed');
        });
    }

});
