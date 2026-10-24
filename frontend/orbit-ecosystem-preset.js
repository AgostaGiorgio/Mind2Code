/** * Orbit Design System - Dark Theme
 */
export default {
  theme: {
    extend: {
      colors: {
        brand: {
          background: '#0f172a',
          surface: '#1e293b',
          primary: '#8b5cf6',
          secondary: '#c084fc',
          textMain: '#f8fafc',
          textMuted: '#94a3b8',
        }
      },
      borderRadius: {
        'app': '24px',
        'app-sm': '12px',
      },
      boxShadow: {
        'app': '0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)',
      },
      fontSize: {
        'app-title': ['2rem', { lineHeight: '2.5rem', fontWeight: '700' }],
        'app-body': ['1rem', { lineHeight: '1.5rem', fontWeight: '500' }],
      }
    }
  }
}
