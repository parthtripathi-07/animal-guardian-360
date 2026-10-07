'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { Languages } from 'lucide-react';

export default function LanguageSwitcher({ currentLocale }: { currentLocale: string }) {
  const pathname = usePathname();
  const router = useRouter();

  const toggleLanguage = () => {
    const nextLocale = currentLocale === 'en' ? 'hi' : 'en';

    // Replace current locale prefix in path
    let newPath = pathname;
    if (pathname.startsWith(`/${currentLocale}`)) {
      newPath = pathname.replace(`/${currentLocale}`, `/${nextLocale}`);
    } else {
      newPath = `/${nextLocale}${pathname}`;
    }

    router.push(newPath);
  };

  return (
    <button
      onClick={toggleLanguage}
      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-300 text-xs font-bold hover:bg-slate-50 dark:hover:bg-slate-800 hover:text-emerald-600 transition-colors shadow-sm"
      title={currentLocale === 'en' ? 'हिंदी में बदलें (Switch to Hindi)' : 'Switch to English (अंग्रेज़ी में बदलें)'}
    >
      <Languages className="w-4 h-4 text-emerald-600" />
      <span>{currentLocale === 'en' ? 'हिंदी' : 'English'}</span>
    </button>
  );
}

