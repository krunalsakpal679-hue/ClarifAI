import type { Config } from 'tailwindcss';

const config: Config = {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    screens: {
      sm: '640px',   // Tablet (640px - 1024px)
      md: '768px',   // Mid-Tablet
      lg: '1024px',  // Laptop (1024px - 1440px)
      xl: '1440px',  // Desktop (1440px - 1920px)
      '2xl': '1920px', // Large Desktop (>1920px with max-width constraint)
    },
    extend: {
      colors: {
        // PRD 23.1 Color Palette Tokens
        primary: {
          DEFAULT: '#1B2A4A', // Brand, headers, primary text on light surfaces
          navy: '#1B2A4A',
          dark: '#121C33',
          light: '#243760',
        },
        accent: {
          DEFAULT: '#2E5AAC', // Deep Blue: buttons, links, focus states, active elements
          hover: '#24488A',
          light: '#EBF1FA',
          active: '#1D3B73',
        },
        neutral: {
          surface: '#FFFFFF',
          subtle: '#F7F8FA',   // Page background
          border: '#C9CFD9',   // Card borders, dividers
          'text-secondary': '#5B6472', // Secondary/supporting text
          'text-primary': '#1B2A4A',   // Primary text
        },
        risk: {
          high: {
            DEFAULT: '#B23B3B', // High severity badge/icon
            bg: '#FDF2F2',
            border: '#F8B4B4',
            text: '#991B1B',
          },
          moderate: {
            DEFAULT: '#C77B22', // Moderate severity badge/icon
            bg: '#FEF8F0',
            border: '#FBD38D',
            text: '#9C4221',
          },
          low: {
            DEFAULT: '#B08D1F', // Low severity badge/icon
            bg: '#FEFDF0',
            border: '#F6E05E',
            text: '#744210',
          },
          safe: {
            DEFAULT: '#2F7D5A', // Safe badge/icon
            bg: '#F0FDF4',
            border: '#9AE6B4',
            text: '#22543D',
          },
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      fontSize: {
        // PRD 23.2 Typography Scale
        display: ['3rem', { lineHeight: '1.15', fontWeight: '700' }], // 48px (44-56px range)
        h1: ['2rem', { lineHeight: '1.25', fontWeight: '700' }],      // 32px
        h2: ['1.5rem', { lineHeight: '1.3', fontWeight: '600' }],     // 24px
        h3: ['1.25rem', { lineHeight: '1.35', fontWeight: '600' }],   // 20px (18-20px range)
        body: ['0.9375rem', { lineHeight: '1.5', fontWeight: '400' }],// 15px (15-16px range)
        'body-lg': ['1rem', { lineHeight: '1.5', fontWeight: '400' }],// 16px
        caption: ['0.75rem', { lineHeight: '1.4', fontWeight: '500' }],// 12px
        label: ['0.8125rem', { lineHeight: '1.4', fontWeight: '500' }],// 13px (12-13px range)
      },
      borderRadius: {
        // PRD 23.3 Radius Tokens
        control: '6px', // Small controls: buttons, inputs
        card: '12px',   // Cards (10-12px)
        modal: '16px',  // Modals/overlays
      },
      boxShadow: {
        // PRD 23.3 Elevation Tokens
        'elevation-0': 'none',
        'elevation-1': '0 1px 3px 0 rgba(27, 42, 74, 0.08), 0 1px 2px -1px rgba(27, 42, 74, 0.08)',
        'elevation-2': '0 4px 6px -1px rgba(27, 42, 74, 0.12), 0 2px 4px -2px rgba(27, 42, 74, 0.08)',
        'elevation-3': '0 10px 15px -3px rgba(27, 42, 74, 0.15), 0 4px 6px -4px rgba(27, 42, 74, 0.10)',
      },
      transitionDuration: {
        // PRD 23.6 Motion Principles
        micro: '200ms',  // 150-250ms for micro-interactions
        page: '350ms',   // 300-400ms for page/section transitions
      },
      maxWidth: {
        constrained: '1440px', // Large Desktop centered max-width constraint
      },
    },
  },
  plugins: [],
};

export default config;
