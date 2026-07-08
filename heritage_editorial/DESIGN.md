---
name: Heritage Editorial
colors:
  surface: '#fbf9f5'
  surface-dim: '#dbdad6'
  surface-bright: '#fbf9f5'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f5f3ef'
  surface-container: '#efeeea'
  surface-container-high: '#eae8e4'
  surface-container-highest: '#e4e2de'
  on-surface: '#1b1c1a'
  on-surface-variant: '#4e4637'
  inverse-surface: '#30312e'
  inverse-on-surface: '#f2f0ed'
  outline: '#807665'
  outline-variant: '#d1c5b2'
  surface-tint: '#795900'
  primary: '#6f5100'
  on-primary: '#ffffff'
  primary-container: '#8b6914'
  on-primary-container: '#fff0da'
  inverse-primary: '#ecc165'
  secondary: '#5f5e5e'
  on-secondary: '#ffffff'
  secondary-container: '#e2dfde'
  on-secondary-container: '#636262'
  tertiary: '#34568c'
  on-tertiary: '#ffffff'
  tertiary-container: '#4e6fa6'
  on-tertiary-container: '#eff2ff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdfa0'
  primary-fixed-dim: '#ecc165'
  on-primary-fixed: '#261a00'
  on-primary-fixed-variant: '#5c4300'
  secondary-fixed: '#e5e2e1'
  secondary-fixed-dim: '#c8c6c5'
  on-secondary-fixed: '#1c1b1b'
  on-secondary-fixed-variant: '#474746'
  tertiary-fixed: '#d6e3ff'
  tertiary-fixed-dim: '#aac7ff'
  on-tertiary-fixed: '#001b3e'
  on-tertiary-fixed-variant: '#23477b'
  background: '#fbf9f5'
  on-background: '#1b1c1a'
  surface-variant: '#e4e2de'
typography:
  display-lg:
    fontFamily: Playfair Display
    fontSize: 64px
    fontWeight: '600'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Playfair Display
    fontSize: 40px
    fontWeight: '600'
    lineHeight: '1.2'
  headline-md:
    fontFamily: Playfair Display
    fontSize: 32px
    fontWeight: '500'
    lineHeight: '1.3'
  section-label:
    fontFamily: Playfair Display
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.12em
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
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.02em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  max_width: 1280px
  section_v_spacing: 120px
  desktop_padding: 80px
  tablet_padding: 40px
  mobile_padding: 20px
  gutter: 24px
---

## Brand & Style

This design system is built for a premium cultural heritage platform, drawing inspiration from high-end art galleries and modern museum archives. The aesthetic is "Gallery-Clean"—characterized by expansive white space, sophisticated serif-driven editorial layouts, and a warm, archival color palette.

The brand personality is authoritative yet inviting, treating digital artifacts with the same reverence as physical exhibits. The design style blends **Minimalism** with **Editorial** sensibilities, using structured grids and refined typography to create a sense of timelessness and discovery. The UI should feel quiet and unobtrusive, allowing high-resolution cultural imagery to remain the focal point.

## Colors

The palette is rooted in "Warm Gallery Whites" and "Light Parchment" tones to avoid the sterile feel of pure digital white. 

- **Primary Accent:** Heritage Gold (#8B6914) is used sparingly for links and interactive highlights, evoking the richness of historical artifacts.
- **Surface Strategy:** Use the primary background for the main canvas. Use secondary and accent backgrounds to differentiate content sections (e.g., a "Related Exhibits" footer).
- **Typography Contrast:** Primary text is a soft black to maintain readability without the harshness of pure #000. Tertiary text is reserved for metadata and the specific section-label pattern.

## Typography

The typographic hierarchy relies on the contrast between the expressive, high-contrast **Playfair Display** and the functional, neutral **Inter**.

- **Display & Headlines:** Always set in Playfair Display. Use for titles and large editorial quotes.
- **Section Labels:** These use a smaller, wide-tracked serif (mimicking Cormorant Garamond's elegance) to act as navigational anchors.
- **Body Text:** Inter provides a legible, contemporary counterpoint to the traditional serifs, ensuring that long-form descriptions remain accessible and clear.
- **Editorial Touch:** For pull-quotes or featured captions, use Playfair Display Italic to enhance the "museum journal" feel.

## Layout & Spacing

The layout follows a **Fixed Grid** philosophy on desktop to maintain the integrity of editorial compositions, transitioning to a fluid model on smaller devices.

- **Vertical Rhythm:** Large gaps of 120px between major sections are essential to create "breathing room," mimicking the physical space between exhibits in a gallery.
- **Grid Strategy:** Use a 12-column grid for desktop. Images should often span 6 or 8 columns, while text blocks are narrowed to 4 or 6 columns to ensure optimal line lengths for reading.
- **Adaptation:** On mobile, vertical spacing should reduce to 64px, and horizontal padding to 20px, with content reflowing into a single column.

## Elevation & Depth

This design system avoids heavy shadows and floating layers in favor of **Tonal Layers** and subtle depth markers.

- **The "Artifact" Card:** Content cards use a pure white (#FFFFFF) background to pop against the warm parchment pages. Depth is suggested by a single, crisp, low-opacity shadow (0 1px 3px rgba(0,0,0,0.06)).
- **Outlines:** Use 1px borders (#D8D2CA) to define boundaries without adding visual weight.
- **Interactive Depth:** On hover, images should not lift with shadows but rather scale slightly (1.03x) within their containers to suggest a "looking closer" effect.

## Shapes

The shape language is primarily architectural and sharp, emphasizing the grid. 

- **Corners:** Use a "Soft" radius (4px) for interactive elements like buttons and input fields to prevent the UI from feeling aggressive, while maintaining a classic look. 
- **Media:** Cultural imagery and hero banners should remain perfectly square (0px) to preserve their "framed art" appearance.

## Components

### Section Headers
A core signature of the design system. Combine a `section-label` (uppercase, letter-spaced) followed by a 1px horizontal line (#D8D2CA) that spans the remaining width of the container or column.

### Buttons
- **Primary:** 1px #1A1A1A solid outline, 4px corner radius, Inter SemiBold. On hover, the button fills with #1A1A1A and text becomes #FAF8F4.
- **Heritage Link:** Text-only link in #8B6914. Feature a "sliding underline" animation—a 1px underline that grows from left-to-right on hover.

### Artifact Cards
Pure white background, 4px radius, 1px #D8D2CA border. Imagery should be top-aligned with no internal padding; text content follows below with 24px internal padding.

### Input Fields
Minimalist 1px #D8D2CA bottom border only for a "form" feel, or a full 4px rounded light stroke. Focus state transitions the border to #8B6914.

### Animations
Implement a global "Scroll Reveal" where elements fade in and move up by 30px as they enter the viewport. Transitions should be slow (600ms - 800ms) and use a "cubic-bezier(0.16, 1, 0.3, 1)" easing for a graceful, high-end feel.