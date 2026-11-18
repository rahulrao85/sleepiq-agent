# Sleep IQ — Image Prompts for Submission

---

## 1. Logo

**Tool:** Any AI image generator (DALL-E, Midjourney, Stable Diffusion)

**Prompt:**

> A minimal, professional logo for "Sleep IQ" — an AI sleep health companion. A crescent moon cradling a brain wave pattern that subtly forms a checkmark. Deep navy and soft indigo palette with a gradient accent of violet-blue. Clean, medical-grade aesthetic. No text, just the symbol. Vector-style, flat design with subtle glow.

**Usage:** Replace the "Z" (💤) emoji in `ui_template.py` line 84. Search for `font-size: 22px; font-weight: 700; color: #fff;` — that's the logo div. Replace the emoji text with an `<img src="logo.png">` tag.

---

## 2. Hero Image for Innovation Studio Submission

**Prompt:**

> A split visualization of sleep health data analysis. Left side: a dark bedroom with a person sleeping, a CPAP machine glowing softly blue, and a smartwatch on the wrist displaying heart rate data. Right side: a high-tech dashboard overlay showing flowing charts, AI analysis text, and medical citations floating in holographic cards. Color palette: deep navy background (#080b16), indigo and violet gradient accents. Cinematic lighting, photorealistic with subtle UI elements floating. 16:9 aspect ratio, 4K quality.

---

## 3. Architecture Diagram Visual

**Prompt:**

> A clean, modern architecture diagram showing a multi-agent AI system flowing from left to right. Left: data sources (CPAP machine icon, Apple Watch, Fitbit, Garmin). Middle: an "Azure AI Foundry" brain icon with four labeled agent nodes — "Data Ingestion", "Trend Analysis", "Risk Assessment", "Recommendation". Right: a "Doctor Report" icon. Below: an "Azure AI Search" database icon labeled "Medical Knowledge". Dark theme with indigo/blue color scheme. Professional, presentation-ready, no text needed beyond labels. Flat design with subtle 3D depth. 16:9 aspect ratio.

---

## 4. Social Media Card (Discord/GitHub)

**Prompt:**

> A sleek social media card for a sleep health AI app called "Sleep IQ". Tagline: "Your sleep. Decoded." Background: deep space navy gradient with a subtle brain wave pattern. Center: a glowing crescent moon icon with pulse line. Bottom: "Built for Microsoft Agents League @ AI Skills Fest 2026". Dark theme, premium health-tech aesthetic. 1200x630 pixels (Open Graph standard). No person faces, keep it abstract and medical.

---

## How to Use These

| Image | Where It Goes | Format |
|-------|---------------|--------|
| Logo | `ui_template.py` — replace "Z" emoji in header | PNG, 48x48 or SVG |
| Hero Image | Innovation Studio submission (first visual) | PNG/JPG, 1920x1080 |
| Architecture | Innovation Studio submission + `architecture.md` | PNG, 1920x1080 |
| Social Card | GitHub repo social preview + Discord share | PNG, 1200x630 |
