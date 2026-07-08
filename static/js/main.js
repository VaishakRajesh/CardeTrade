/* ============================================================
   CardeTrade — Premium UI/UX JavaScript v2.0
   ============================================================
   WHAT THIS FILE DOES:
   --------------------
   This file adds interactivity and animations to the CardeTrade
   website. All code runs when the page loads (DOMContentLoaded).

   FEATURES:
    1. Preloader: Hides loading spinner after page loads
    2. Navbar Scroll: Makes navbar opaque when scrolling down
    3. Scroll Animations: Elements fade/slide in when visible
    4. Counter: Numbers count up from 0 to target value
    5. Alerts: Auto-dismiss success/error messages after 5s
    6. 3D Tilt: Cards tilt based on mouse position
    7. Parallax: Hero image moves slowly when scrolling
    8. Particles: Floating dots in hero section background
    9. Active Nav: Highlights current page in navbar
    10. Quantity Calc: Live price calculation on purchase page
    11. Tooltips: Bootstrap tooltip initialization
    12. Confetti: Celebration confetti burst
    13. Scroll Progress: Top progress bar on page scroll
    14. Ripple Effect: Click ripple animation on buttons
    15. Smooth Scroll: Smooth anchor link scrolling
    16. Table Hover: Subtle table row hover effect
    17. Notification Pulse: Heartbeat animation on bell
    18. Chat Scroll: Auto-scroll chat to bottom
    19. Navbar Toggle: Mobile menu animation
   ============================================================ */

// Wait for the HTML to be fully loaded before running our code
document.addEventListener('DOMContentLoaded', function() {

    'use strict';  // Catch common coding mistakes

    // ==========================================================
    // 1. PRELOADER — Hide loading spinner
    //    The #preloader div covers the page while content loads.
    //    After page load (or 1.8s timeout), we fade it out.
    // ==========================================================
    const preloader = document.getElementById('preloader');
    if (preloader) {
        // Try to hide immediately after all assets load (images, etc.)
        window.addEventListener('load', function() {
            setTimeout(function() { preloader.classList.add('hidden'); }, 400);
        });
        // Fallback: hide after 1.8 seconds even if not fully loaded
        setTimeout(function() { preloader.classList.add('hidden'); }, 1800);
    }

    // ==========================================================
    // 2. NAVBAR SCROLL EFFECT
    //    When user scrolls down > 80px, add 'scrolled' class
    //    to navbar. CSS makes it opaque with glass effect.
    // ==========================================================
    const navbar = document.querySelector('.navbar-premium');
    if (navbar) {
        window.addEventListener('scroll', function() {
            // Toggle 'scrolled' class based on scroll position
            navbar.classList.toggle('scrolled', window.scrollY > 80);
        }, { passive: true });  // passive: true for better scroll performance
    }

    // ==========================================================
    // 3. SCROLL ANIMATIONS (IntersectionObserver)
    //    Detects when elements scroll into view, then adds
    //    a 'visible' class to trigger CSS animations.
    // ==========================================================
    function setupScrollAnimations(selector, className) {
        // Find all elements with the given selector
        const els = document.querySelectorAll(selector);
        if (!els.length) return;  // No elements found, skip
        
        // Create an observer that watches when elements enter viewport
        const obs = new IntersectionObserver(function(entries) {
            entries.forEach(function(e) {
                if (e.isIntersecting) {
                    // Element is visible — add class to animate it in
                    e.target.classList.add(className || 'visible');
                }
            });
        }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });  // Trigger when 8% visible

        // Start watching all matching elements
        els.forEach(function(el) { obs.observe(el); });
    }
    
    // Set up scroll animations for different directions
    setupScrollAnimations('.animate-on-scroll');        // Fade in + slide up
    setupScrollAnimations('.animate-on-scroll-left');   // Slide in from left
    setupScrollAnimations('.animate-on-scroll-right');  // Slide in from right
    setupScrollAnimations('.animate-on-scroll-scale');  // Scale up

    // ==========================================================
    // 4. COUNTER ANIMATION (requestAnimationFrame)
    //    Numbers on stat cards count up from 0 when they scroll
    //    into view. Uses requestAnimationFrame for smooth 60fps.
    // ==========================================================
    const counters = document.querySelectorAll('.stat-number, .counter-value');
    counters.forEach(function(el) {
        const target = parseInt(el.getAttribute('data-target') || el.textContent.replace(/[^0-9]/g, '')) || 0;
        if (target === 0) { el.textContent = '0'; return; }

        const duration = 1800;
        let startTime = null;
        let started = false;

        function tick(timestamp) {
            if (!startTime) startTime = timestamp;
            const elapsed = timestamp - startTime;
            const progress = Math.min(elapsed / duration, 1);
            el.textContent = Math.round(progress * target);
            if (progress < 1) requestAnimationFrame(tick);
        }

        const obs = new IntersectionObserver(function(entries) {
            if (!entries[0].isIntersecting || started) return;
            started = true;
            requestAnimationFrame(tick);
            obs.unobserve(el);
        }, { threshold: 0.3 });

        obs.observe(el);
    });

    // ==========================================================
    // 5. ALERTS AUTO-DISMISS
    //    Success/error messages auto-hide after 5 seconds.
    //    Uses Bootstrap's alert API to animate close.
    // ==========================================================
    document.querySelectorAll('.alert-dismissible').forEach(function(a) {
        setTimeout(function() {
            try {
                // Bootstrap 5 method to close alert
                bootstrap.Alert.getOrCreateInstance(a).close();
            } catch(e) {}  // Silently ignore if Bootstrap isn't available
        }, 5000);  // 5 seconds
    });

    // ==========================================================
    // 6. CARD HOVER TILT EFFECT (3D)
    //    Cards tilt in 3D space based on mouse position.
    //    Uses CSS perspective + rotateX/Y transforms.
    //    Creates a subtle 3D parallax effect on card hover.
    // ==========================================================
    document.querySelectorAll('.card-premium, .listing-card-premium, .feature-card-premium').forEach(function(card) {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();  // Card position on screen
            const x = e.clientX - rect.left;  // Mouse X relative to card
            const y = e.clientY - rect.top;   // Mouse Y relative to card
            const cx = rect.width / 2;         // Center X of card
            const cy = rect.height / 2;        // Center Y of card
            // Calculate rotation: further from center = more tilt
            const rx = (y - cy) / 18;  // Rotate X (tilt forward/back)
            const ry = (cx - x) / 18;  // Rotate Y (tilt left/right)
            card.style.transform = 'perspective(1000px) rotateX(' + rx + 'deg) rotateY(' + ry + 'deg) translateY(-4px)';
        });
        // Reset transform when mouse leaves
        card.addEventListener('mouseleave', function() {
            card.style.transform = '';
        });
    });

    // ==========================================================
    // 7. PARALLAX ON HERO IMAGE
    //    Hero background image moves slightly when scrolling.
    //    Speed is 12% of scroll position (slower than scroll).
    //    Creates depth effect: image moves slower than content.
    // ==========================================================
    const heroImg = document.querySelector('.hero-overlay img');
    if (heroImg) {
        window.addEventListener('scroll', function() {
            const sy = window.scrollY;
            // Only apply parallax while hero is visible
            if (sy < window.innerHeight) {
                heroImg.style.transform = 'translateY(' + (sy * 0.12) + 'px) scale(1.08)';
            }
        }, { passive: true });
    }

    // ==========================================================
    // 8. HERO PARTICLE GENERATOR
    //    Creates 20 floating particles in the hero background.
    //    Each particle is randomly positioned and has different
    //    size, animation speed, delay, and opacity.
    // ==========================================================
    const particleContainer = document.querySelector('.hero-particles');
    if (particleContainer && particleContainer.children.length === 0) {
        // Create 20 particles with random properties
        for (let i = 0; i < 20; i++) {
            const p = document.createElement('div');
            p.className = 'particle';
            // Random position, size, animation delay, duration, opacity
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
    //    Highlights the current page's nav link by adding
    //    'active' class. Compares link href with current URL.
    // ==========================================================
    const path = window.location.pathname;
    document.querySelectorAll('.navbar-premium .nav-link').forEach(function(link) {
        const href = link.getAttribute('href');
        if (href && href !== '/' && path.startsWith(href)) {
            link.classList.add('active');  // Match by URL prefix
        } else if (href === '/' && path === '/') {
            link.classList.add('active');  // Exact match for homepage
        }
    });

    // ==========================================================
    // 10. QUANTITY CALCULATOR (Direct Buy page)
    //     When user types quantity on purchase page, show
    //     live calculation of total price and quantity.
    // ==========================================================
    document.querySelectorAll('input[name="quantity_kg"]').forEach(function(input) {
        input.addEventListener('input', function() {
            // Find the price element in the same form
            const form = this.closest('form');
            const priceEl = form ? form.querySelector('[data-price]') : null;
            if (!priceEl) return;
            
            const ppkg = parseFloat(priceEl.dataset.price) || 0;  // Price per kg
            const qty = parseFloat(this.value) || 0;              // User-entered qty
            const total = document.getElementById('totalDisplay');
            const qtyD = document.getElementById('qtyDisplay');
            
            if (total) total.textContent = 'Rs ' + (ppkg * qty).toFixed(2);  // Update total
            if (qtyD) qtyD.textContent = qty;                                 // Update qty display
        });
    });

    // ==========================================================
    // 11. TOOLTIPS — Bootstrap tooltip initialization
    //     Activates Bootstrap tooltips on elements with
    //     data-bs-toggle="tooltip" attribute.
    // ==========================================================
    try {
        var tt = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tt.map(function(el) { return new bootstrap.Tooltip(el); });
    } catch(e) {}  // Fail silently if Bootstrap JS not loaded



    // ==========================================================
    // 13. SCROLL PROGRESS INDICATOR
    //     A thin bar at the very top of the page showing
    //     how far the user has scrolled (0% to 100%).
    //     Gold gradient color matching the site theme.
    // ==========================================================
    const scrollProgress = document.createElement('div');
    scrollProgress.style.cssText = 'position:fixed;top:0;left:0;height:3px;background:linear-gradient(90deg,var(--accent),var(--gold));z-index:99999;transition:width 0.1s;';
    document.body.appendChild(scrollProgress);
    
    window.addEventListener('scroll', function() {
        const h = document.documentElement;
        // Calculate percentage: scrollTop / (total height - viewport height)
        const pct = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100;
        scrollProgress.style.width = pct + '%';
    }, { passive: true });

    // ==========================================================
    // 14. RIPPLE EFFECT ON BUTTONS
    //     When user clicks a .btn-premium button, a ripple
    //     (expanding circle) emanates from the click point.
    //     Uses @keyframes rippleEffect in CSS.
    // ==========================================================
    document.querySelectorAll('.btn-premium').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            const ripple = document.createElement('span');
            const rect = this.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);  // Square size for the circle
            
            // Position ripple at click point, relative to button
            ripple.style.cssText = [
                'position:absolute;border-radius:50%;',
                'width:' + size + 'px;height:' + size + 'px;',
                'left:' + (e.clientX - rect.left - size/2) + 'px;',
                'top:' + (e.clientY - rect.top - size/2) + 'px;',
                'background:rgba(255,255,255,0.3);',
                'animation:rippleEffect 0.6s ease-out forwards;',
                'pointer-events:none;'  /* Don't block clicks */
            ].join('');
            
            // Ensure button has position:relative for absolute positioning
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(ripple);
            
            // Remove ripple element after animation
            setTimeout(function() { ripple.remove(); }, 700);
        });
    });

    // ==========================================================
    // 15. SMOOTH SCROLL FOR ANCHOR LINKS
    //     Links starting with "#" smoothly scroll to the
    //     target element instead of jumping.
    // ==========================================================
    document.querySelectorAll('a[href^="#"]').forEach(function(a) {
        a.addEventListener('click', function(e) {
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                e.preventDefault();  // Stop default jump behavior
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });

    // ==========================================================
    // 16. TABLE ROW HOVER HIGHLIGHT (CSS class toggle)
    //     Premium table rows scale up slightly and add shadow
    //     on hover, creating a subtle depth effect.
    // ==========================================================
    document.querySelectorAll('.table-premium tbody tr').forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.classList.add('table-row-hover');
        });
        row.addEventListener('mouseleave', function() {
            this.classList.remove('table-row-hover');
        });
    });



    // ==========================================================
    // 18. CHAT AUTO-SCROLL TO BOTTOM
    //     When viewing a conversation, automatically scroll
    //     to the latest message at the bottom.
    // ==========================================================
    const chatContainer = document.querySelector('.chat-container');
    if (chatContainer) {
        chatContainer.scrollTop = chatContainer.scrollHeight;  // Scroll to bottom
    }

    // ==========================================================
    // 19. NAVBAR TOGGLE ANIMATION
    //     Toggle 'collapsed' class on hamburger button for
    //     custom styling of the mobile menu toggle.
    // ==========================================================
    const navbarToggler = document.querySelector('.navbar-premium .navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            this.classList.toggle('collapsed');
        });
    }

});  // End of DOMContentLoaded
