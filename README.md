# KuruDash

A fully local homelab service dashboard with built-in SSH terminal, custom backgrounds, and liquid glass UI.
No backend. No database. No tracking. One HTML file.

---

## Overview

KuruDash gives you a clean, organized view of all your self-hosted services from a single browser tab.
Add services, group them into folders, monitor their uptime, and SSH directly into your servers — all without running any server-side code. Everything is stored in your browser's localStorage and never leaves your device.

---

## Features

**Core**
- Single HTML file — no Node.js, no Docker, no build step required
- All data stored locally in localStorage, never transmitted anywhere
- Service status polling every 60 seconds with live up/down indicators
- Auto favicon fetching from service URLs
- Drag and drop card reordering
- Collapsible folder tree for organizing services
- JSON export and import for backup and migration

**SSH Terminal**
- Full in-browser SSH terminal powered by xterm.js
- Connects to a WebSocket relay (ttyd or webssh2) running on your server
- Multiple concurrent sessions in tabbed panels
- Copy SSH command to clipboard or launch via ssh:// protocol handler

**Themes**
- 12 built-in themes: Aero, Aero Dark, Dark, Mocha, Nord, Solarized, Sakura, Sakura Dark, Terminal, Flat Dark, Flat Light, Custom
- Full custom theme builder with color picker for all surface colors
- Dark mode variants for every major theme including Sakura Dark

**Custom Backgrounds**
- Upload a local image file (saved as base64, max 5MB)
- Paste any direct image URL
- Build a gradient with a 3-stop color picker and direction selector
- Fine-tune overlay opacity, panel blur strength, and card transparency
- Auto-pick accent color from your background image
- Off by default — toggle on in Settings
- Reset to default theme background at any time without affecting service data

**Performance**
- Lightweight mode in Settings disables all backdrop-filter and blur effects for low-spec devices
- CSS will-change on animated elements to reduce reflow
- Background rendering uses a dedicated composited layer

---

## Getting Started

**Option 1 — Download and open**

Download dashboard.html and open it in any modern browser. No internet connection required after initial font load.

**Option 2 — Clone the repository**

```
git clone https://github.com/YOUR_USERNAME/kurudash
```

Open dashboard.html directly from the cloned folder.

---

## SSH Terminal Setup

KuruDash's terminal connects to a WebSocket relay on your server. No proxy or backend is required on KuruDash's side.

**Option A — ttyd (recommended for simplicity)**

```bash
apt install ttyd           # Debian / Ubuntu
brew install ttyd           # macOS

ttyd -p 7681 bash           # shell relay
ttyd -p 7681 login          # login prompt
```

Connect using ws://YOUR_SERVER_IP:7681 in the service SSH settings.

**Option B — webssh2 (full SSH authentication)**

```bash
git clone https://github.com/billchurch/webssh2
cd webssh2/app && npm install && npm start
```

Default relay address: ws://YOUR_SERVER_IP:2222

**Connecting in KuruDash**

1. Add or edit a service
2. Open the Connection tab
3. Set Connection Type to SSH
4. Enter username and port
5. Enter the WebSocket relay URL
6. Save, then click "Open SSH Terminal" from the properties panel or double-click the card

---

## Custom Background Setup

1. Open Settings (gear icon in the header)
2. Scroll to Custom Background
3. Toggle "Enable custom background" on
4. Choose a source: URL, Upload, or Gradient
5. For URL: paste a direct image link and click Apply
6. For Upload: choose a local image file (jpg, png, webp, max 5MB)
7. For Gradient: pick three colors, choose a direction, click Apply Gradient
8. Use the sliders to adjust overlay opacity, panel blur, and card transparency
9. Click "Auto-pick accent from image" to match accent color to the wallpaper

Background settings are stored separately. Clicking "Reset to default" clears only visual options, leaving all service data intact.

---

## Performance on Low-Spec Devices

If blur effects cause slowdown on older hardware, open Settings, scroll to Performance, and enable Lightweight mode. This disables all backdrop-filter and blur effects while keeping the rest of the UI fully functional.

---

## Backup and Restore

1. Open Settings and scroll to Backup & Restore
2. Click Export JSON to download, or Copy to clipboard
3. To restore: paste JSON into the textarea and click Import JSON

The export includes services, folders, theme selection, and custom theme colors. Background images are not included in the export (stored separately as base64).

---

## Repository Structure

```
kurudash/
├── dashboard.html      The entire application
├── index.html          Landing page (optional, for GitHub Pages)
├── README.md           This file
├── LICENSE             GPL v3
├── icons/              UI icons and avatar (PNG with SVG fallbacks)
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
```

---

## Privacy

No backend, no analytics, no tracking, no cookies. Network requests made by the app:

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
