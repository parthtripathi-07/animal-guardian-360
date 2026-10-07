'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Sparkles, MapPin, Camera, AlertCircle, ArrowLeft, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';
import { useGeolocation } from '@/hooks/useGeolocation';
import { apiClient } from '@/lib/api-client';

export default function NewLostFoundPostPage({ params: { locale } }: { params: { locale: string } }) {
  const router = useRouter();
  const { coords, loading: geoLoading } = useGeolocation();

  const [postType, setPostType] = useState<'lost' | 'found' | 'sighting'>('lost');
  const [species, setSpecies] = useState('dog');
  const [breed, setBreed] = useState('');
  const [primaryColor, setPrimaryColor] = useState('');
  const [secondaryColor, setSecondaryColor] = useState('');
  const [gender, setGender] = useState('unknown');
  const [distinctiveMarks, setDistinctiveMarks] = useState('');
  const [collarInfo, setCollarInfo] = useState('');
  const [address, setAddress] = useState('');
  const [photoUrl, setPhotoUrl] = useState('');

  const [loading, setLoading] = useState(false);
  const [dpdpConsent, setDpdpConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createdPost, setCreatedPost] = useState<any>(null);


  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!coords) {
      setError('GPS coordinates are required to run spatial proximity matching');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const payload = {
        post_type: postType,
        species,
        breed: breed || undefined,
        primary_color: primaryColor || undefined,
        secondary_color: secondaryColor || undefined,
        gender: gender || undefined,
        distinctive_marks: distinctiveMarks || undefined,
        collar_info: collarInfo || undefined,
        latitude: coords.latitude,
        longitude: coords.longitude,
        address_text: address || 'Current GPS coordinates',
        photo_urls: photoUrl ? [photoUrl] : [],
        masked_contact_enabled: true,
      };

      const res = await apiClient<any>('/pets/posts', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setCreatedPost(res);
    } catch (err: any) {
      setError(err.message || 'Failed to submit post');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        <Link
          href={`/${locale}/lost-and-found`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to listings
        </Link>

        {!createdPost ? (
          <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
            <div>
              <h1 className="text-2xl font-black text-slate-900">Post Lost or Found Pet</h1>
              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                Visual embeddings will search opposite reports within 25 km automatically.
              </p>
            </div>

            {error && (
              <div className="p-4 bg-red-50 text-red-700 text-sm rounded-xl border border-red-200 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Post Type Selector */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-2">Report Type</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { id: 'lost', label: '🔴 Lost Pet', desc: 'My pet is missing' },
                  { id: 'found', label: '🟢 Found Pet', desc: 'I have rescued a pet' },
                  { id: 'sighting', label: '👀 Sighting', desc: 'I spotted a roaming pet' },
                ].map((type) => (
                  <button
                    key={type.id}
                    type="button"
                    onClick={() => setPostType(type.id as any)}
                    className={`p-3.5 rounded-xl border text-left transition-all ${
                      postType === type.id
                        ? 'bg-blue-600 text-white border-blue-600 shadow-sm'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    <div className="text-xs font-black">{type.label}</div>
                    <div className="text-[10px] opacity-80 mt-0.5">{type.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Species & Breed */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Species</label>
                <select
                  value={species}
                  onChange={(e) => setSpecies(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl bg-white outline-none"
                >
                  <option value="dog">Dog</option>
                  <option value="cat">Cat</option>
                  <option value="bird">Bird</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Breed (if known)</label>
                <input
                  type="text"
                  placeholder="e.g. Golden Retriever, Indie, Persian"
                  value={breed}
                  onChange={(e) => setBreed(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
                />
              </div>
            </div>

            {/* Colors & Gender */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Primary Color</label>
                <input
                  type="text"
                  placeholder="e.g. Golden, Black, White"
                  value={primaryColor}
                  onChange={(e) => setPrimaryColor(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Secondary Color</label>
                <input
                  type="text"
                  placeholder="e.g. Tan, White chest"
                  value={secondaryColor}
                  onChange={(e) => setSecondaryColor(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Gender</label>
                <select
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl bg-white outline-none"
                >
                  <option value="unknown">Unknown</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </div>
            </div>

            {/* Distinctive Marks & Collar */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Collar / Tag Info</label>
                <input
                  type="text"
                  placeholder="e.g. Red nylon collar with bell"
                  value={collarInfo}
                  onChange={(e) => setCollarInfo(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Distinctive Marks</label>
                <input
                  type="text"
                  placeholder="e.g. White patch on forehead, docked tail"
                  value={distinctiveMarks}
                  onChange={(e) => setDistinctiveMarks(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
                />
              </div>
            </div>

            {/* Location & GPS */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Last Seen Location / Area</label>
              <input
                type="text"
                placeholder="e.g. Near Deer Park, Hauz Khas"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none mb-2"
              />
              <div className="flex items-center text-xs text-slate-500 bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <MapPin className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                {coords
                  ? `GPS Attached: ${coords.latitude.toFixed(4)}, ${coords.longitude.toFixed(4)}`
                  : 'Detecting GPS coordinates...'}
              </div>
            </div>

            {/* Photo URL */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-1">Photo Image URL</label>
              <input
                type="url"
                placeholder="https://example.com/pet.jpg (Required for visual embedding)"
                value={photoUrl}
                onChange={(e) => setPhotoUrl(e.target.value)}
                className="w-full text-sm p-3 border border-slate-200 rounded-xl outline-none"
              />
            </div>

            {/* DPDP Act 2023 Consent Checkbox */}
            <div className="flex items-start gap-3 p-3.5 bg-blue-50/60 rounded-xl border border-blue-200/80">
              <input
                type="checkbox"
                id="pet-dpdp-consent"
                required
                checked={dpdpConsent}
                onChange={(e) => setDpdpConsent(e.target.checked)}
                className="w-4 h-4 mt-0.5 accent-blue-600 rounded cursor-pointer"
              />
              <label htmlFor="pet-dpdp-consent" className="text-xs text-slate-700 leading-relaxed cursor-pointer">
                I consent to the processing of the pet photo for AI visual embedding generation and storage of contact details under the <Link href="/privacy" target="_blank" className="text-blue-700 underline font-semibold">Digital Personal Data Protection Act, 2023</Link> with in-app masked contact relay.
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !dpdpConsent}
              className="w-full py-4 rounded-xl bg-blue-600 hover:bg-blue-700 text-white font-black text-sm uppercase tracking-wider shadow-lg shadow-blue-600/20 transition-transform active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Generating Embeddings...' : 'Publish Listing & Run AI Match'}</span>
            </button>

          </form>
        ) : (
          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm text-center space-y-6">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle2 className="w-10 h-10" />
            </div>

            <div>
              <h2 className="text-2xl font-black text-slate-900">Pet Listing Published!</h2>
              <p className="text-sm text-slate-500 mt-1">
                Visual embeddings generated and cross-referenced across posts within 25 km.
              </p>
            </div>

            {createdPost.matches && createdPost.matches.length > 0 ? (
              <div className="bg-indigo-50 p-5 rounded-2xl border border-indigo-100 text-left space-y-3">
                <div className="flex items-center gap-2 text-indigo-900 font-extrabold text-sm">
                  <Sparkles className="w-4 h-4 text-indigo-600" />
                  <span>Found {createdPost.matches.length} Instant AI Match(es)!</span>
                </div>
                {createdPost.matches.map((m: any) => (
                  <div key={m.match_id} className="bg-white p-3.5 rounded-xl border border-indigo-100 flex items-center justify-between text-xs">
                    <div>
                      <div className="font-bold text-slate-800 capitalize">
                        {m.breed || m.species} ({m.matched_post_type.toUpperCase()})
                      </div>
                      <div className="text-slate-500">{m.address_text || 'Nearby'} · {m.distance_km} km away</div>
                    </div>
                    <span className="font-black text-indigo-600 bg-indigo-50 px-2.5 py-1 rounded-full">
                      {m.confidence_percent}% Match
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-4 bg-slate-50 rounded-xl text-slate-600 text-xs border border-slate-200">
                No immediate matches above threshold found within 25 km. You will be notified instantly when a matching sighting is posted!
              </div>
            )}

            <button
              onClick={() => router.push(`/${locale}/lost-and-found/${createdPost.id}`)}
              className="w-full py-3 bg-slate-900 text-white font-bold text-sm rounded-xl"
            >
              View Listing & Live Tracking
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
