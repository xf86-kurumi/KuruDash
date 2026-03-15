# KuruDash

A fully local homelab service dashboard with built-in SSH terminal, live stat widgets, custom backgrounds, and liquid glass UI.
No backend. No database. No tracking. One HTML file.

---

## Overview

KuruDash gives you a clean, organized view of all your self-hosted services from a single browser tab.
Add services, group them into folders, monitor their uptime, pull live stats from Netdata or any JSON API, and SSH directly into your servers — all without running any server-side code. Everything is stored in your browser's localStorage and never leaves your device.

---

## Features

**Core**
- Single HTML file — no Node.js, no Docker, no build step required
- All data stored locally in localStorage, never transmitted anywhere
- Service status polling every 60 seconds with live up/down indicators
- Debounced renders via `requestAnimationFrame` — smooth, zero jank during mass status checks
- Tab visibility-aware polling — pauses when the tab is hidden to save resources
- Staggered initial status checks (150ms apart) to prevent network hammering on load
- Auto favicon fetching from service URLs with fallback to built-in SVG icons
- Drag and drop card reordering within and across folders
- Collapsible folder tree with folder summary cards at root view showing up/down/total counts
- JSON export and import for backup and migration
- Color-coded response time — green under 200ms, yellow under 600ms, red above
- Search with inline highlight of matching text in card names and IPs
- Pin services to keep them at the top of the grid
- Per-service notes
- Lock screen with 4-digit PIN

**Widgets**
- Live stat tiles displayed above the service grid, refreshed every 8 seconds
- 10 preset types: CPU Load, RAM Usage, Disk Usage, Network In, Power Draw, Temperature, Uptime, Load Avg, Docker Containers, Custom
- Custom widget type for any JSON endpoint
- Configurable data URL, JSON path (dot notation), unit, warn threshold, alert threshold
- Color-coded progress bar — green/yellow/red based on thresholds
- Pauses polling when browser tab is hidden
- Works with Netdata, Prometheus node_exporter, Home Assistant, Docker API, smart plug APIs, or any custom JSON endpoint
- Widgets included in export/import/clear

**SSH Terminal**
- Full in-browser SSH terminal powered by xterm.js
- Connects to a WebSocket relay (ttyd or webssh2) running on your server
- Multiple concurrent sessions in tabbed panels
- Split pane mode for two terminals side by side
- Copy SSH command to clipboard or launch via ssh:// protocol handler
- Adjustable font size and command snippets

**Themes**
- 12 built-in themes: Aero, Aero Dark, Dark, Mocha, Nord, Solarized, Sakura, Sakura Dark, Terminal, Flat Dark, Flat Light, Custom
- Full custom theme builder with color picker for all surface colors

**Custom Backgrounds**
- Upload a local image file (saved as base64, max 5MB)
- Paste any direct image URL
- Build a gradient with a 3-stop color picker and direction selector
- Fine-tune overlay opacity, panel blur strength, and card transparency
- Auto-pick accent color from your background image

**Performance**
- GPU compositing layers on all glass elements (`will-change: transform`, `translateZ(0)`)
- Reduced backdrop-filter values (24–28px) tuned for visual quality without jank
- `prefers-reduced-motion` respected — all animations disabled automatically
- Lightweight mode disables all blur effects for low-spec devices

---

## Getting Started

**Option 1 — Download and open**

Download `dashboard.html` and open it in any modern browser. No internet connection required after the initial font load.

**Option 2 — Clone the repository**

```bash
git clone https://github.com/xf86-kurumi/KuruDash/
```

Open `dashboard.html` directly from the cloned folder.

---

## Widget Setup

Widgets pull live data from any URL that returns JSON. The easiest path is **Netdata** — a free, zero-config monitoring agent that exposes a full REST API instantly on port 19999.

### Step 1 — Install Netdata on each server you want to monitor

```bash
curl https://my-netdata.io/kickstart.sh | sh
```

That is all. Netdata starts automatically and is available at `http://YOUR_SERVER_IP:19999`. No configuration needed.

### Step 2 — Add a widget in KuruDash

1. Click the bar chart icon in the header (or press `W`)
2. Pick a preset — CPU, RAM, Disk, Power, etc.
3. Paste the data URL for your server
4. Adjust the label, unit, warn/alert thresholds if needed
5. Click **Add Widget**

The widget appears in the strip above your service grid and refreshes every 8 seconds.

### Netdata URL reference

Replace `192.168.1.100` with your server's actual IP address.

| Widget | URL |
|--------|-----|
| CPU % | `http://192.168.1.100:19999/api/v1/data?chart=system.cpu&points=1&after=-1` |
| RAM % | `http://192.168.1.100:19999/api/v1/data?chart=system.ram&points=1&after=-1` |
| Disk % | `http://192.168.1.100:19999/api/v1/data?chart=disk_space._&points=1&after=-1` |
| Network in KB/s | `http://192.168.1.100:19999/api/v1/data?chart=system.net&points=1&after=-1` |
| Temperature °C | `http://192.168.1.100:19999/api/v1/data?chart=sensors.coretemp&points=1&after=-1` |
| Load average | `http://192.168.1.100:19999/api/v1/data?chart=system.load&points=1&after=-1` |

All Netdata responses return `{ "data": [[value, ...]] }` — the default JSON path `data.0.0` works for all of them.

### Docker container count

Point the Containers preset at the Docker API socket proxy (or a lightweight API wrapper like [docker-proxy](https://github.com/Tecnativa/docker-socket-proxy)):

```
URL:  http://192.168.1.100:2375/v1/info
Path: ContainersRunning
```

### Power draw (smart plugs and UPS)

Any smart plug or UPS with an HTTP API works. Examples:

**Shelly plug** — returns `{"apower": 87.4}`
```
URL:  http://192.168.1.50/rpc/Switch.GetStatus?id=0
Path: apower
Unit: W
```

**TP-Link Tapo / Kasa** — use a local API wrapper like [python-kasa](https://github.com/python-kasa/python-kasa) with a simple HTTP shim.

**APC UPS / Network UPS Tools (NUT)** — expose a JSON endpoint via the NUT web interface or a small Python script, then point the Power widget at it.

### Custom widget for any JSON

Pick the Custom preset and fill in any URL that returns JSON. Use dot notation for the path — for example if your endpoint returns:

```json
{ "stats": { "temperature": 54.2 } }
```

Set path to `stats.temperature`.

### Fixing CORS errors

Browsers block requests to other origins by default. If a widget shows "Error", you need to enable CORS on the server side.

**For Netdata**, edit `/etc/netdata/netdata.conf`:

```ini
[web]
    allow connections from = *
    bind to = 0.0.0.0
    access control allow origin = *
```

Then restart: `sudo systemctl restart netdata`

**For any other API**, add the header `Access-Control-Allow-Origin: *` to the response. Most reverse proxies (nginx, Caddy, Traefik) can add this with one line.

**Simplest alternative** — open KuruDash from the same machine as the server, where there is no cross-origin restriction.

---

## SSH Terminal Setup

KuruDash's terminal connects to a WebSocket relay on your server. No proxy or backend is required on the KuruDash side.

**Option A — ttyd (recommended)**

```bash
apt install ttyd        # Debian / Ubuntu
brew install ttyd       # macOS

ttyd -p 7681 bash       # shell relay (no login)
ttyd -p 7681 login      # login prompt with authentication
```

Then in KuruDash, add or edit a service → Connection tab → set type to SSH → enter `ws://192.168.1.100:7681`.

**Option B — webssh2 (full SSH key/password auth)**

```bash
git clone https://github.com/billchurch/webssh2
cd webssh2/app && npm install && npm start
```

Default relay address: `ws://YOUR_SERVER_IP:2222`

**Connecting**

1. Add or edit a service
2. Open the Connection tab
3. Set Connection Type to SSH
4. Enter username and port
5. Enter the WebSocket relay URL
6. Save — then double-click the card or click Open SSH Terminal in the properties panel

---

## Custom Background Setup

1. Open Settings → Background tab
2. Toggle Enable custom background on
3. Choose URL, Upload, or Gradient
4. Use the sliders to adjust overlay opacity, panel blur, and card transparency
5. Click Auto-pick accent to match the accent color to your wallpaper

Background settings are stored separately. Resetting clears only visual options, leaving all service data intact.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `A` | Add new service |
| `F` | Focus search box |
| `S` | Open Settings |
| `T` | Toggle SSH terminal panel |
| `V` | Toggle grid / list view |
| `W` | Open Widgets panel |
| `Esc` | Close open panel or modal |

---

## Performance on Low-Spec Devices

Open Settings → Interface → enable Lightweight mode. This disables all `backdrop-filter` and blur effects. The dashboard also respects the OS Reduce Motion accessibility setting automatically — all animations are disabled if the user has that enabled.

---

## Backup and Restore

Settings → Data tab → Export JSON (download or copy to clipboard).

To restore: paste the JSON and click Import. The export includes services, folders, theme, custom theme colors, widget configurations, notes, and pinned IDs. Background images are stored separately as base64 and excluded from export due to size.

---

## Repository Structure

```
kurudash/
├── dashboard.html      The entire application
├── index.html          Landing page (optional, for GitHub Pages)
├── README.md           This file
├── LICENSE             GPL v3
├── icons/              UI icons (PNG with built-in SVG fallbacks)
└── docs/               Screenshots for the landing page
```

---

## Themes

| Name | Description |
|------|-------------|
| Aero | Frutiger Aero light — glassy sky blues (default) |
| Aero Dark | Deep navy with cyan accents |
| Dark | GitHub-style dark |
| Mocha | Catppuccin Mocha |
| Nord | Nord palette |
| Solarized | Solarized Light |
| Sakura | Pink and cherry blossom light |
| Sakura Dark | Deep rose dark with pink accents |
| Terminal | Classic green on black |
| Flat Dark | Flat UI dark |
| Flat Light | Flat UI light |
| Custom | Build your own with the color picker |

---

## localStorage Keys

```
kurudash-tree           Services and folder structure
kurudash-collapsed      Collapsed folder state
kurudash-theme          Selected theme
kurudash-custom-theme   Custom theme colors
kurudash-bg             Background image or gradient CSS
kurudash-bg-type        Background source type
kurudash-bg-opts        Overlay opacity, blur, card transparency
kurudash-perf-mode      Lightweight mode state
kurudash-ui             Clock, compact header, notifications prefs
kurudash-notes          Per-service notes
kurudash-pinned         Pinned service IDs
kurudash-snippets       SSH command snippets
kurudash-ssh-font       SSH terminal font size
kurudash-lock-pin       Lock screen PIN (stored locally only)
kurudash-custom-css     User-injected custom CSS
kurudash-widgets        Widget configurations
```

---

## Privacy

No backend, no analytics, no tracking, no cookies. Network requests made by the app:

- Status checks to your own service URLs
- Widget data fetches to URLs you configure
- Favicon fetching from your own service URLs
- Google Fonts on first load (Instrument Serif, Outfit, DM Mono)
- xterm.js from cdnjs on first load

All of the above can be replaced with self-hosted alternatives.

---

## Browser Compatibility

| Browser | Status |
|---------|--------|
| Firefox 78+ | Full support |
| Chrome / Edge 80+ | Full support |
| Safari 14+ | Full support |
| Older browsers | Partial — backdrop-filter may not work |

---

## Credits

Icons — Aoi (hand-drawn icons and logo)
Code, UI design, and project concept — xf86-kurumi
SSH terminal — xterm.js
Fonts — Instrument Serif, Outfit, DM Mono via Google Fonts
Hosting — Cloudflare Pages

---

## License

GNU General Public License v3.0

    KuruDash — homelab service dashboard
    Copyright (C) 2024 KuruDash Contributors

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
