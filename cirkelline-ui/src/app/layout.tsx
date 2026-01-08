import type { Metadata } from 'next'
import { DM_Mono, Geist } from 'next/font/google'
import { NuqsAdapter } from 'nuqs/adapters/next/app'
import { Toaster } from '@/components/ui/sonner'
import { AuthProvider } from '@/contexts/AuthContext'
import { LearnMoreProvider } from '@/contexts/LearnMoreContext'
import './globals.css'
const geistSans = Geist({
  variable: '--font-geist-sans',
  weight: '400',
  subsets: ['latin']
})

const dmMono = DM_Mono({
  subsets: ['latin'],
  variable: '--font-dm-mono',
  weight: '400'
})

export const metadata: Metadata = {
  title: 'Cirkelline - Your Personal AI Assistant',
  description:
    'Cirkelline is your intelligent personal assistant powered by multi-agent AI system',
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
      { url: '/favicon.svg', sizes: '32x32', type: 'image/svg+xml' },
      { url: '/favicon.svg', sizes: '16x16', type: 'image/svg+xml' }
    ],
    shortcut: '/favicon.svg',
    apple: '/favicon.svg'
  }
}

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  // Initialize theme
                  const theme = localStorage.getItem('theme');
                  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                  const initialTheme = theme || (prefersDark ? 'dark' : 'light');
                  if (initialTheme === 'dark') {
                    document.documentElement.classList.add('dark');
                  } else {
                    document.documentElement.classList.remove('dark');
                  }

                  // Initialize accent color - DEFAULT TO 'contrast'
                  let accentColor = localStorage.getItem('accentColor');
                  if (!accentColor) {
                    accentColor = 'contrast';
                    localStorage.setItem('accentColor', 'contrast');
                  }

                  // Apply accent color immediately
                  const isDark = document.documentElement.classList.contains('dark');
                  let rgbValue;

                  if (accentColor === 'contrast') {
                    // DARK theme: button bg WHITE (#E0E0E0), text BLACK
                    // LIGHT theme: button bg BLACK (#212124), text WHITE
                    rgbValue = isDark ? '224, 224, 224' : '33, 33, 36';
                  } else {
                    const colorMap = {
                      purple: '142, 11, 131',
                      orange: '236, 75, 19',
                      green: '19, 236, 129',
                      blue: '19, 128, 236',
                      pink: '236, 19, 128'
                    };
                    rgbValue = colorMap[accentColor] || '224, 224, 224';
                  }

                  document.documentElement.style.setProperty('--accent-rgb', rgbValue);
                } catch (e) {}
              })();
            `,
          }}
        />
      </head>
      <body className={`${geistSans.variable} ${dmMono.variable} antialiased bg-light-bg dark:bg-dark-bg text-light-text dark:text-dark-text`} suppressHydrationWarning>
        <AuthProvider>
          <LearnMoreProvider>
            <NuqsAdapter>{children}</NuqsAdapter>
            <Toaster />
          </LearnMoreProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
