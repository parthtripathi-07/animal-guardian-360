import Link from 'next/link';
import { AlertCircle, ShieldAlert, Search, Heart, MapPin } from 'lucide-react';
import { useTranslations } from 'next-intl';

export default function HomePage({ params: { locale } }: { params: { locale: string } }) {
  const t = useTranslations('home');

  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-emerald-900 via-slate-900 to-slate-900 text-white py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-5xl mx-auto text-center space-y-6">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
            {t('badge')}
          </span>
          <h1 className="text-4xl sm:text-6xl font-black tracking-tight leading-tight">
            {t('heroTitle')} <br />
            <span className="text-emerald-400">{t('heroHighlight')}</span>
          </h1>
          <p className="text-slate-300 text-base sm:text-lg max-w-2xl mx-auto">
            {t('heroSubtitle')}
          </p>

          {/* Big SOS Button */}
          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href={`/${locale}/vets`}
              className="w-full sm:w-auto px-8 py-4 bg-red-600 hover:bg-red-700 text-white font-black text-lg rounded-2xl shadow-xl shadow-red-600/30 transition-transform active:scale-95 flex items-center justify-center gap-3 border border-red-500"
            >
              <AlertCircle className="w-6 h-6 animate-pulse" />
              <span>{t('sosBtn')}</span>
            </Link>
            <Link
              href={`/${locale}/vets`}
              className="w-full sm:w-auto px-8 py-4 bg-white/10 hover:bg-white/20 text-white font-bold text-base rounded-2xl backdrop-blur transition-colors flex items-center justify-center gap-2 border border-white/20"
            >
              <MapPin className="w-5 h-5 text-emerald-400" />
              <span>{t('findVetsBtn')}</span>
            </Link>
          </div>
        </div>
      </section>

      {/* 4 Pillars Feature Grid */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900">{t('pillarsTitle')}</h2>
          <p className="text-slate-500 text-sm mt-1">{t('pillarsSubtitle')}</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Card 1 */}
          <Link
            href={`/${locale}/vets`}
            className="group bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-500 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 bg-red-50 text-red-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <AlertCircle className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900">{t('cardVetsTitle')}</h3>
              <p className="text-slate-500 text-xs mt-2 leading-relaxed">
                {t('cardVetsDesc')}
              </p>
            </div>
            <div className="text-emerald-600 text-xs font-bold mt-6 flex items-center gap-1">
              <span>{t('cardVetsTitle')} →</span>
            </div>
          </Link>

          {/* Card 2 */}
          <Link
            href={`/${locale}/cruelty-report`}
            className="group bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-500 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <ShieldAlert className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900">{t('cardCrueltyTitle')}</h3>
              <p className="text-slate-500 text-xs mt-2 leading-relaxed">
                {t('cardCrueltyDesc')}
              </p>
            </div>
            <div className="text-emerald-600 text-xs font-bold mt-6 flex items-center gap-1">
              <span>{t('cardCrueltyTitle')} →</span>
            </div>
          </Link>

          {/* Card 3 */}
          <Link
            href={`/${locale}/lost-and-found`}
            className="group bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-500 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Search className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900">{t('cardPetsTitle')}</h3>
              <p className="text-slate-500 text-xs mt-2 leading-relaxed">
                {t('cardPetsDesc')}
              </p>
            </div>
            <div className="text-emerald-600 text-xs font-bold mt-6 flex items-center gap-1">
              <span>{t('cardPetsTitle')} →</span>
            </div>
          </Link>

          {/* Card 4 */}
          <Link
            href={`/${locale}/donate`}
            className="group bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md hover:border-emerald-500 transition-all flex flex-col justify-between"
          >
            <div>
              <div className="w-12 h-12 bg-rose-50 text-rose-600 rounded-xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                <Heart className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-lg text-slate-900">{t('cardDonateTitle')}</h3>
              <p className="text-slate-500 text-xs mt-2 leading-relaxed">
                {t('cardDonateDesc')}
              </p>
            </div>
            <div className="text-emerald-600 text-xs font-bold mt-6 flex items-center gap-1">
              <span>{t('cardDonateTitle')} →</span>
            </div>
          </Link>
        </div>
      </section>
    </div>
  );
}
