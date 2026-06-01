---
name: Cinematic Industrial
colors:
  surface: '#131317'
  surface-dim: '#131317'
  surface-bright: '#39393d'
  surface-container-lowest: '#0e0e12'
  surface-container-low: '#1b1b1f'
  surface-container: '#1f1f23'
  surface-container-high: '#2a292e'
  surface-container-highest: '#353439'
  on-surface: '#e5e1e7'
  on-surface-variant: '#bdc8d1'
  inverse-surface: '#e5e1e7'
  inverse-on-surface: '#303034'
  outline: '#87929a'
  outline-variant: '#3e484f'
  surface-tint: '#7bd0ff'
  primary: '#8ed5ff'
  on-primary: '#00354a'
  primary-container: '#38bdf8'
  on-primary-container: '#004965'
  inverse-primary: '#00668a'
  secondary: '#bdc2ff'
  on-secondary: '#131e8c'
  secondary-container: '#2f3aa3'
  on-secondary-container: '#a8afff'
  tertiary: '#56e5a9'
  on-tertiary: '#003824'
  tertiary-container: '#30c88f'
  on-tertiary-container: '#004e34'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#c4e7ff'
  primary-fixed-dim: '#7bd0ff'
  on-primary-fixed: '#001e2c'
  on-primary-fixed-variant: '#004c69'
  secondary-fixed: '#e0e0ff'
  secondary-fixed-dim: '#bdc2ff'
  on-secondary-fixed: '#000767'
  on-secondary-fixed-variant: '#2f3aa3'
  tertiary-fixed: '#6ffbbe'
  tertiary-fixed-dim: '#4edea3'
  on-tertiary-fixed: '#002113'
  on-tertiary-fixed-variant: '#005236'
  background: '#131317'
  on-background: '#e5e1e7'
  surface-variant: '#353439'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 48px
    fontWeight: '800'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 36px
    fontWeight: '800'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 28px
    fontWeight: '700'
    lineHeight: '1.3'
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '700'
    lineHeight: '1.3'
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 20px
    fontWeight: '700'
    lineHeight: '1.4'
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: '1.6'
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
  label-caps:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: '1'
    letterSpacing: 0.1em
  mono-data:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: -0.01em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  base: 4px
  xs: 8px
  sm: 16px
  md: 24px
  lg: 32px
  xl: 48px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 40px
---

## Brand & Style
The design system is engineered for high-stakes industrial environments, blending the high-density information architecture of a Bloomberg Terminal with the refined, cinematic aesthetics of a luxury automotive interface. It targets heavy industry decision-makers who require an authoritative and high-tech command center.

The style is **Institutional Glassmorphism**. It utilizes ultra-dark surfaces to minimize eye strain in control rooms while using vibrant, neon-inspired accents to highlight critical AI insights. The aesthetic is defined by deep spatial depth, precision-engineered borders, and atmospheric glows that suggest a "living" intelligence behind the data.

## Colors
This design system operates on a "Total Dark" philosophy. The palette is anchored by a deep black foundation to create infinite depth, allowing the accent colors to function as light sources within the UI.

- **Primary Cyan:** Used for active states, primary actions, and "AI-driven" highlights. It should be treated as a neon light source.
- **Secondary Indigo:** Used for secondary structural elements and data groupings.
- **Success/Warning:** Reserved strictly for status indicators and high-priority alerts.
- **Surfaces:** Transitions from `#050508` (Base) to `#12141D` (Elevated) provide the necessary hierarchy for complex ERP dashboards without breaking the cinematic immersion.

## Typography
The typography strategy creates a tension between industrial strength and digital precision. **Plus Jakarta Sans** is used for headers in Bold and ExtraBold weights to provide a commanding, modern presence. **Inter** handles all functional and body text, ensuring maximum legibility in data-heavy industrial tables.

For numerical data (KPIs, sensor readings), use the `mono-data` style to ensure alignment and readability during rapid fluctuations. Use `label-caps` for table headers and section overlines to maintain an institutional, organized feel.

## Layout & Spacing
The layout follows a **Fixed-Fluid Hybrid Grid**. Main dashboard containers utilize a 12-column system on desktop with a 24px gutter. For high-density ERP modules, a secondary "compact" grid mode is available where spacing is halved.

- **Desktop:** 12 columns, 40px margins.
- **Tablet:** 8 columns, 24px margins.
- **Mobile:** 4 columns, 16px margins.

Spacing follows a 4px base unit, but emphasizes generous outer margins (40px+) to maintain the premium, "uncluttered" feel of a high-end dashboard. Content should be grouped into logical "Modules" that behave like physical glass panels.

## Elevation & Depth
Depth is the core differentiator of the design system. It avoids traditional drop shadows in favor of **Layered Glassmorphism** and **Luminous Outlines**.

1.  **Surfaces:** All containers use a 20px backdrop-blur and a 6% opacity white border to define edges against the deep black background.
2.  **Atmospheric Glows:** Use subtle, large-radius radial gradients (`#38BDF8` or `#818CF8` at 5-10% opacity) positioned behind primary modules to create a "haloing" effect, suggesting the importance of the data.
3.  **Dot Grid:** A subtle 16px x 16px dot-grid pattern (`#ffffff` at 3% opacity) sits on the background layer to provide a sense of scale and industrial precision.
4.  **Z-Index Hierarchy:** 
    - Level 0: Background with dot-grid.
    - Level 1: Standard Glass Modules.
    - Level 2: Hovered/Selected states with Primary Cyan inner-glow.
    - Level 3: Overlays and Modals with intensified backdrop blur (40px).

## Shapes
The shape language is "Soft-Industrial." To maintain an authoritative and technical feel, the design system avoids hyper-rounded "pill" shapes for primary containers.

- **Containers/Cards:** Use `rounded-lg` (8px) for a structured look.
- **Buttons/Inputs:** Use `rounded` (4px) to emphasize precision.
- **Status Indicators:** Use `0px` (Sharp) for small decorative accents or 50% (Circle) for status pips.

The goal is to feel engineered rather than playful.

## Components
Consistent component styling reinforces the "Industrial Command Center" aesthetic.

- **Buttons:** Primary buttons use a solid Cyan fill with black text. Secondary buttons use a transparent background with the 6% white border and a cyan hover glow.
- **Input Fields:** Semi-transparent dark background, 1px border. On focus, the border animates to Primary Cyan with a subtle 4px outer bloom.
- **Data Cards:** Every card must feature the 20px backdrop-blur. Include a "Label-Caps" header in the top left and a technical "ID Code" (e.g., FX-99) in the top right for industrial flavor.
- **Status Chips:** Small, condensed capsules. Use "Success Emerald" text with a 10% opacity Emerald background—no solid fills unless the status is critical.
- **Progress Bars:** Use a thin 4px track. The fill should be a linear gradient from Secondary Indigo to Primary Cyan.
- **AI Insights:** Any AI-generated content should be framed with a subtle Cyan-to-Transparent gradient border and a low-intensity radial glow behind the text.