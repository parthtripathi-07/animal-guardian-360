'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, MapPin, Plus, Filter, Sparkles, CheckCircle2 } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { LostFoundPostResponse } from '@/types';

export default function LostAndFoundPage({ params: { locale } }: { params: { locale: string } }) {
  const [posts, setPosts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [postType, setPostType] = useState<string>('');
  const [species, setSpecies] = useState<string>('');
  const [searchBreed, setSearchBreed] = useState<string>('');

  const fetchPosts = async () => {
    setLoading(true);
    try {
      const queryParams = new URLSearchParams();
      if (postType) queryParams.append('post_type', postType);
      if (species) queryParams.append('species', species);
      if (searchBreed) queryParams.append('breed', searchBreed);

      const data = await apiClient<any[]>(`/pets/posts?${queryParams.toString()}`);
      setPosts(data);
    } catch (e) {
      console.error('Failed to fetch posts:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPosts();
  }, [postType, species]);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Banner */}
        <div className="bg-gradient-to-r from-blue-700 via-indigo-700 to-blue-800 rounded-2xl p-6 sm:p-8 text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center md:text-left">
            <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-white/20 text-white uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" /> AI Vector Matching Powered
            </span>
            <h1 className="text-2xl sm:text-4xl font-black tracking-tight">
              Lost & Found Pets Network
            </h1>
            <p className="text-blue-100 text-sm max-w-xl">
              Post lost pets or recent community sightings. Our visual embedding engine automatically
              matches photos against records within 25 km and notifies owners.
            </p>
          </div>

          <Link
            href={`/${locale}/lost-and-found/new`}
            className="w-full md:w-auto px-6 py-3.5 bg-white text-blue-700 hover:bg-blue-50 font-black rounded-xl text-sm shadow-lg transition-transform active:scale-95 shrink-0 flex items-center justify-center gap-2"
          >
            <Plus className="w-5 h-5" />
            <span>REPORT LOST / FOUND PET</span>
          </Link>
        </div>

        {/* Filter Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-2">
            {/* Post Type Filters */}
            {[
              { id: '', label: 'All Listings' },
              { id: 'lost', label: '🔴 Lost Pets' },
              { id: 'found', label: '🟢 Found Pets' },
              { id: 'sighting', label: '👀 Sightings' },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setPostType(tab.id)}
                className={`px-3.5 py-1.5 text-xs font-bold rounded-lg transition-colors ${
                  postType === tab.id
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-3">
            {/* Species Filter */}
            <select
              value={species}
              onChange={(e) => setSpecies(e.target.value)}
              className="text-xs font-bold bg-slate-50 border border-slate-200 rounded-lg p-2 outline-none"
            >
              <option value="">All Species</option>
              <option value="dog">Dogs</option>
              <option value="cat">Cats</option>
              <option value="bird">Birds</option>
              <option value="other">Other</option>
            </select>

            {/* Breed search */}
            <div className="flex items-center bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5">
              <input
                type="text"
                placeholder="Search breed..."
                value={searchBreed}
                onChange={(e) => setSearchBreed(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && fetchPosts()}
                className="text-xs bg-transparent outline-none w-28 sm:w-36"
              />
              <button onClick={fetchPosts}>
                <Search className="w-3.5 h-3.5 text-slate-400" />
              </button>
            </div>
          </div>
        </div>

        {/* Listings Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">
              Community Pet Listings ({posts.length})
            </h2>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-64 bg-slate-200 animate-pulse rounded-2xl" />
              ))}
            </div>
          ) : posts.length === 0 ? (
            <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
              <Search className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No Listings Found</h3>
              <p className="text-xs text-slate-500 mt-1">Try resetting your filters or post a new pet alert.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
              {posts.map((post) => (
                <Link
                  key={post.id}
                  href={`/${locale}/lost-and-found/${post.id}`}
                  className="group bg-white rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col justify-between"
                >
                  <div>
                    {/* Image / Thumbnail */}
                    <div className="relative h-44 bg-slate-100 flex items-center justify-center overflow-hidden">
                      {post.photo_urls && post.photo_urls[0] ? (
                        <img
                          src={post.photo_urls[0]}
                          alt={post.species}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                        />
                      ) : (
                        <div className="text-slate-400 text-xs font-semibold uppercase tracking-wider">
                          No Photo Uploaded
                        </div>
                      )}

                      <div className="absolute top-2.5 left-2.5">
                        <span
                          className={`text-xs font-extrabold uppercase px-2.5 py-1 rounded-full shadow-sm ${
                            post.post_type === 'lost'
                              ? 'bg-red-600 text-white'
                              : post.post_type === 'found'
                              ? 'bg-emerald-600 text-white'
                              : 'bg-blue-600 text-white'
                          }`}
                        >
                          {post.post_type}
                        </span>
                      </div>

                      {post.status === 'reunited' && (
                        <div className="absolute top-2.5 right-2.5 bg-emerald-500 text-white text-xs font-bold px-2 py-0.5 rounded-full flex items-center gap-1 shadow-sm">
                          <CheckCircle2 className="w-3 h-3" /> Reunited
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="p-4 space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="font-bold text-base text-slate-900 capitalize">
                          {post.breed || post.species}
                        </h3>
                        <span className="text-xs font-semibold text-slate-500 capitalize">
                          {post.species}
                        </span>
                      </div>

                      <div className="flex items-center text-xs text-slate-500 truncate">
                        <MapPin className="w-3.5 h-3.5 mr-1 text-slate-400 shrink-0" />
                        <span className="truncate">{post.address_text || 'GPS recorded'}</span>
                      </div>

                      <div className="text-xs text-slate-400">
                        {new Date(post.incident_date).toLocaleDateString([], {
                          month: 'short',
                          day: 'numeric',
                        })}
                      </div>
                    </div>
                  </div>

                  {/* AI Match Badge footer */}
                  {post.matches && post.matches.length > 0 && (
                    <div className="p-3 bg-indigo-50 border-t border-indigo-100 flex items-center justify-between text-xs font-bold text-indigo-700">
                      <span className="flex items-center gap-1">
                        <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
                        {post.matches.length} AI Match Found
                      </span>
                      <span>{post.matches[0].confidence_percent}% Match</span>
                    </div>
                  )}
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
