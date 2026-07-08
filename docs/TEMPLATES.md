# UI/UX Design Guide — CardeTrade

## Design Philosophy

- **Premium cardamom-themed aesthetic** — warm greens, golds, and earth tones
- **Glass morphism** — frosted glass cards with backdrop blur
- **Gradient backdrops** — lush green gradients inspired by cardamom plantations
- **Micro-interactions** — 3D tilt on hover, ripple on click, smooth animations
- **Image-forward** — both `cardamom1.jpg` and `cardamom2.jpg` used in every page

## Image Usage Strategy

| Image | Use Case |
|-------|----------|
| `cardamom1.jpg` | Hero banner (main), auth backgrounds, page headers |
| `cardamom2.jpg` | Hero floating accent, gallery cards, secondary headers |

Both images stored at `static/image/cardamom1.jpg` and `static/image/cardamom2.jpg`.

## CSS Class System

### Layout & Cards
- `.premium-card` — glass morphism card with backdrop blur
- `.stat-card` — metric display with icon (6 color variants via inline style)
- `.listing-card` — product listing card with image overlay
- `.timeline-item` — vertical timeline entry
- `.grade-badge-A/B/C` — circular grade indicator with color coding

### Animations (25+ keyframes)
- `fadeInUp` — entrance slide-up
- `glowPulse` — ambient glow breathing
- `float` — gentle floating (hero images)
- `shimmer` — animated gradient text
- `ripple` — button click expansion
- `confetti` — celebration particles
- `particle` — background floating particles
- `countUp` — number counter pop
- `spinSlow` — slow rotation (decorative)

### Interactive Effects
- `.tilt-card` — 3D perspective on mousemove (JS-driven)
- `.btn-ripple` — ripple wave on click (JS-driven)
- `.parallax-hero` — scroll-based movement (JS-driven)
- `.scroll-progress` — reading progress bar (JS-driven)

## Responsive Breakpoints

| Breakpoint | Max Width | Behavior |
|------------|-----------|----------|
| Desktop | >992px | Full layout, side panels |
| Tablet | 992px | 2-col grids, smaller headers |
| Mobile | 768px | Single column, stacked cards |
| Small | 480px | Compact padding, minimal text |

## Page-by-Page Design

### Home (`dashboard/home.html`)
- Full-viewport hero: `cardamom1.jpg` background, `cardamom2.jpg` floating image overlay
- Gradient overlay: `.hero-overlay` with dark green → transparent
- Animated "CardeTrade" title with `.shimmer-text`
- Gallery section: both images in side-by-side cards
- Philosophy section: glass card with decorative elements

### Auth Pages (`auth/login.html`, `auth/register.html`)
- Full-screen background: `cardamom1.jpg` with blur overlay
- Glass card form: `.premium-card` centered
- Logo: `cardamom2.jpg` circular thumbnail above form
- Animated entrance: form slides up on load

### Batch List (`batches/list.html`)
- Page header: `cardamom1.jpg` with overlay and page title
- Table rows: hover effect, status badges with color coding
- Right sidebar: premium filter card

### Trading Listings (`trading/listing_list.html`)
- Header: `cardamom2.jpg` backdrop
- Cards: `.listing-card` with image, price, type badge
- Price per kg prominently displayed

### Messaging (`messaging/conversation_detail.html`)
- Chat bubbles: `.msg-bubble.sent` (right, green) / `.msg-bubble.received` (left, white)
- Auto-scroll to bottom on load (JS)
- Conversation sidebar with participant avatars

### Disputes (`disputes/list.html`)
- Header banner with `cardamom1.jpg`
- Dispute table with status badges (open/yellow, resolved/green)
- PM/Admin: Resolve button in action column

### Notifications (`notifications/list.html`)
- Timeline-style list with type icons
- Unread indicator (green dot)
- Navbar dropdown: last 5 notifications with heartbeat pulse
