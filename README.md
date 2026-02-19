# 📈 STOCKINTEL — Real-Time Stock Market Intelligence and Decision Support Platform

> Capstone Project — Graduate Computer Science, New Jersey Institute of Technology  
---

## 👥 Project Team

| Name | Role |
|---|---|
| Monil Baxi | Team Leader · Full Stack Developer |
| Youganon Saikia | Backend Developer |
| Shrey Patel | Frontend Developer |
| Deeraj Kumar Vecham Subbaraju | Machine Learning Engineer |

**Faculty Advisor:** Professor Prabhat Vaish

---

## 📋 Executive Summary

STOCKINTEL is a unified web platform that aggregates real-time financial market data, computes advanced technical indicators, and delivers actionable insights through an interactive, responsive UI. It serves as the culminating capstone experience for the NJIT graduate Computer Science program, integrating full-stack development, data pipeline architecture, RESTful API design, and modern frontend engineering.

> ⚠️ **Disclaimer:** This project is for academic and educational purposes only. It is not intended for commercial deployment, real investment decision-making, or financial advisory services.

---

## 🗂️ Project Structure

```
STOCKINTEL/
├── public/                         # Static assets (favicon, og images)
├── src/
│   ├── assets/                     # Images, icons, fonts
│   ├── components/
│   │   └── common/
│   │       └── Button.tsx          # Shared button component
│   ├── pages/
│   │   └── Landing.tsx             # Landing page component
│   ├── App.css                     # Global app styles
│   ├── App.test.tsx                # App-level tests (Vitest)
│   ├── App.tsx                     # Root component & router
│   ├── index.css                   # Tailwind base styles
│   └── main.tsx                    # Vite entry point
├── .gitignore
├── eslint.config.js                # ESLint flat config
├── index.html                      # Vite HTML entry point
├── package.json
├── package-lock.json
├── postcss.config.js               # PostCSS + Tailwind processing
├── README.md
├── tailwind.config.js              # Tailwind CSS configuration
├── tsconfig.json                   # TypeScript base config
├── tsconfig.app.json               # App-specific TS config
├── tsconfig.node.json              # Node/Vite TS config
└── vite.config.ts                  # Vite build configuration
```

---

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/mb2362/stockIntel.git
cd stockIntel
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Start the Development Server

```bash
npm run dev
```

## 🧩 Component Guide

### `src/pages/Landing.tsx`
The main landing page. Renders the hero section, feature cards, stats bar, and CTA. No props required — self-contained route component.

### `src/components/common/Button.tsx`
Shared button primitive used across all pages. Accepts `variant` (`primary` | `secondary`), `onClick`, `children`, and standard HTML button props.

### `src/App.tsx`
Root component. Configures the router and wraps the app in any global providers (theme, auth context, etc.).

### `src/main.tsx`
Vite entry point. Mounts `<App />` into `#root` in `index.html`.

---
![alt text](.\src\assets\screencapture-localhost-3001-2026-02-19-18_37_22.png)
---
## 🤝 Contributing

Team members should follow this Git workflow:

```bash
# Create a feature branch
git checkout -b your_name

# Commit using conventional commits
git commit -m "feat: add RSI chart component"

# Push and open a Pull Request
git push origin your_name
```

**Code standards:**
- TypeScript strict mode enabled — no implicit `any`
- ESLint flat config enforced on all `.ts` / `.tsx` files
- Tailwind utility classes preferred; avoid custom CSS unless necessary
- All exported components and functions must have JSDoc comments

---

## 📬 Contact

**Team Leader:** Monil Baxi — NJIT Graduate CS  
**Repository:** [github.com/mb2362/stockIntel.git](https://github.com/mb2362/stockIntel.git)

---

*STOCKINTEL · NJIT Capstone Project · CS Graduate Program · Spring 2026*