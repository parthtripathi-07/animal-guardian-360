import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import '../globals.css';
import { NextIntlClientProvider } from 'next-intl';
import { getMessages } from 'next-intl/server';
import Link from 'next/link';
import { Shield, AlertCircle, Heart, Search, FileText } from 'lucide-react';
import LanguageSwitcher from '@/components/LanguageSwitcher';
import PWARegistration from '@/components/PWARegistration';

const inter = Inter({ subsets: ['latin'] });

export const viewport = {
  themeColor: '#059669',
  width: 'device-width',
  initialScale: 1,
};

export const metadata: Metadata = {
  title: 'Animal Guardian 360° | Animal Welfare Platform India',
  description: 'Production-ready platform for animal welfare, veterinary rescue, lost pet recovery, cruelty reporting, and donations in India.',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Animal Guardian 360°',
  },
  icons: {
    icon: '/icons/icon-192.png',
    apple: '/icons/icon-192.png',
  },
};

export default async function RootLayout({
  children,
  params: { locale },
}: {
  children: React.ReactNode;
  params: { locale: string };
}) {
  const messages = await getMessages();

  return (
    <html lang={locale}>
      <body className={inter.className}>
        <NextIntlClientProvider messages={messages}>
          <div className="min-h-screen flex flex-col bg-slate-50 text-slate-900">
            {/* Top Navigation */}
            <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <Link href={`/${locale}`} className="flex items-center gap-2">
                  <div className="p-2 bg-emerald-600 rounded-xl text-white shadow-md shadow-emerald-600/20">
                    <Shield className="w-5 h-5" />
                  </div>
                  <span className="font-black text-lg tracking-tight text-slate-900">
                    Animal Guardian <span className="text-emerald-600">360°</span>
                  </span>
                </Link>

                <nav className="hidden md:flex items-center gap-6 text-sm font-semibold text-slate-600">
                  <Link href={`/${locale}/vets`} className="hover:text-emerald-600 transition-colors flex items-center gap-1">
                    <AlertCircle className="w-4 h-4 text-red-500" />
                    <span>Nearby Vets & SOS</span>
                  </Link>
                  <Link href={`/${locale}/cruelty-report`} className="hover:text-emerald-600 transition-colors flex items-center gap-1">
                    <FileText className="w-4 h-4" />
                    <span>Report Cruelty</span>
                  </Link>
                  <Link href={`/${locale}/lost-and-found`} className="hover:text-emerald-600 transition-colors flex items-center gap-1">
                    <Search className="w-4 h-4" />
                    <span>Lost & Found Pets</span>
                  </Link>
                  <Link href={`/${locale}/donate`} className="hover:text-emerald-600 transition-colors flex items-center gap-1">
                    <Heart className="w-4 h-4 text-rose-500" />
                    <span>Donate (80G)</span>
                  </Link>
                  <Link href={`/${locale}/admin/dashboard`} className="hover:text-emerald-600 transition-colors flex items-center gap-1 text-slate-500">
                    <Shield className="w-4 h-4 text-indigo-500" />
                    <span>Admin</span>
                  </Link>
                </nav>

                <div className="flex items-center gap-3">
                  <LanguageSwitcher currentLocale={locale} />
                  <Link
                    href={`/${locale}/vets`}
                    className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white font-bold text-xs rounded-xl shadow-md shadow-red-500/20 transition-all flex items-center gap-1.5"
                  >
                    <AlertCircle className="w-4 h-4 animate-pulse" />
                    <span>SOS EMERGENCY</span>
                  </Link>
                </div>
              </div>
            </header>

            <main className="flex-1">{children}</main>

            <footer className="bg-slate-900 text-slate-400 py-8 text-center text-xs border-t border-slate-800">
              <div className="max-w-7xl mx-auto px-4 space-y-2">
                <p>© 2026 Animal Guardian 360°. Dedicated to rapid animal rescue and welfare across India.</p>
                <div className="flex items-center justify-center gap-4 text-[11px] text-slate-400">
                  <Link href={`/${locale}/privacy`} className="hover:text-emerald-400 underline">
                    Privacy Policy (DPDP Act, 2023)
                  </Link>
                  <span>•</span>
                  <Link href={`/${locale}/donate/transparency`} className="hover:text-emerald-400 underline">
                    Public Transparency Ledger
                  </Link>
                </div>
                <p className="text-[11px] text-slate-500">Emergency Police/Ambulance Helpline: 112 | SPCA National Helpline</p>
              </div>
            </footer>

            <PWARegistration />
          </div>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
