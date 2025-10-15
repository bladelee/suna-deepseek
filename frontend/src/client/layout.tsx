'use client';

import { I18nProvider } from '@/i18n/context';
import { Providers } from '@/app/providers';
import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/components/home/theme-provider';
import { detectLanguage } from '@/i18n';

interface ElectronLayoutProps {
  children: React.ReactNode;
}

export default function ElectronLayout({ children }: ElectronLayoutProps) {
  const detectedLanguage = detectLanguage();

  return (
    <div className="h-screen w-full">
      <ThemeProvider
        attribute="class"
        defaultTheme="system"
        enableSystem
        disableTransitionOnChange
      >
        <I18nProvider defaultLang={detectedLanguage}>
          <Providers>
            {children}
            <Toaster />
          </Providers>
        </I18nProvider>
      </ThemeProvider>
    </div>
  );
}