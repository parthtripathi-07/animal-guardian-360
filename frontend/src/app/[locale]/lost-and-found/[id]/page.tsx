'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import {
  Sparkles,
  MapPin,
  Calendar,
  CheckCircle2,
  ArrowLeft,
  MessageSquare,
  ShieldCheck,
  Tag
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export default function PostDetailsPage({ params: { locale } }: { params: { locale: string } }) {
  const params = useParams();
  const id = params?.id as string;

  const [post, setPost] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchPost = async () => {
    try {
      const data = await apiClient<any>(`/pets/posts/${id}`);
      setPost(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (id) fetchPost();
  }, [id]);

  const handleMarkReunited = async () => {
    if (!confirm('Are you sure you want to mark this pet as reunited?')) return;
    setActionLoading(true);
    try {
      await apiClient(`/pets/posts/${id}/reunited`, { method: 'PATCH' });
      fetchPost();
    } catch (e: any) {
      alert(e.message || 'Failed to update reunited status');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-10 w-10 border-4 border-blue-600 border-t-transparent" />
      </div>
    );
  }

  if (!post) {
    return <div className="p-8 text-center text-slate-500">Listing not found</div>;
  }

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-6">
        <Link
          href={`/${locale}/lost-and-found`}
          className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to listings
        </Link>

        {/* Main Post Card */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden grid grid-cols-1 md:grid-cols-2">
          {/* Photo */}
          <div className="h-64 md:h-full bg-slate-100 relative">
            {post.photo_urls && post.photo_urls[0] ? (
              <img
                src={post.photo_urls[0]}
                alt={post.species}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-slate-400 text-xs uppercase font-bold">
                No Photo Available
              </div>
            )}
            <div className="absolute top-4 left-4">
              <span
                className={`text-xs font-black uppercase px-3 py-1 rounded-full shadow-sm ${
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
          </div>

          {/* Details */}
          <div className="p-6 md:p-8 space-y-4 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <h1 className="text-2xl font-black text-slate-900 capitalize">
                  {post.breed || post.species}
                </h1>
                {post.status === 'reunited' ? (
                  <span className="flex items-center gap-1 text-xs font-bold bg-emerald-100 text-emerald-800 px-2.5 py-1 rounded-full">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Reunited
                  </span>
                ) : (
                  <span className="text-xs font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-full capitalize">
                    {post.status}
                  </span>
                )}
              </div>

              <div className="text-xs text-slate-500 space-y-1 mt-3">
                <div className="flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-slate-400" />
                  <span>{post.address_text || 'GPS coordinates on record'}</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <Calendar className="w-3.5 h-3.5 text-slate-400" />
                  <span>{new Date(post.incident_date).toLocaleString()}</span>
                </div>
              </div>

              {/* Attributes */}
              <div className="grid grid-cols-2 gap-2 text-xs pt-4 border-t border-slate-100 mt-4">
                <div><span className="text-slate-400">Species:</span> <span className="font-bold capitalize">{post.species}</span></div>
                <div><span className="text-slate-400">Gender:</span> <span className="font-bold capitalize">{post.gender || 'Unknown'}</span></div>
                <div><span className="text-slate-400">Color:</span> <span className="font-bold capitalize">{post.primary_color || 'N/A'}</span></div>
                <div><span className="text-slate-400">Secondary:</span> <span className="font-bold capitalize">{post.secondary_color || 'N/A'}</span></div>
              </div>

              {post.distinctive_marks && (
                <div className="mt-3 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                  <span className="font-bold text-slate-700">Marks:</span> {post.distinctive_marks}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="space-y-2 pt-4 border-t border-slate-100">
              {post.status !== 'reunited' && (
                <button
                  onClick={handleMarkReunited}
                  disabled={actionLoading}
                  className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Mark as Reunited</span>
                </button>
              )}

              <button
                onClick={() => alert('Starting masked in-app chat with pet owner/finder...')}
                className="w-full py-2.5 rounded-xl border border-slate-300 hover:bg-slate-50 text-slate-700 font-bold text-xs transition-colors flex items-center justify-center gap-1.5"
              >
                <MessageSquare className="w-4 h-4 text-blue-600" />
                <span>Contact via Masked In-App Chat</span>
              </button>
            </div>
          </div>
        </div>

        {/* AI Matches Section */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 sm:p-8 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-indigo-600" />
                <span>Ranked AI Visual Similarity Matches ({post.matches?.length || 0})</span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Evaluated against opposite listings within 25 km using vector cosine distance
              </p>
            </div>
          </div>

          {post.matches && post.matches.length > 0 ? (
            <div className="space-y-3">
              {post.matches.map((match: any) => (
                <div
                  key={match.match_id}
                  className="p-4 rounded-xl border border-slate-200 hover:border-indigo-400 bg-slate-50 hover:bg-white transition-all flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 rounded-lg bg-slate-200 overflow-hidden shrink-0">
                      {match.matched_photo_url ? (
                        <img
                          src={match.matched_photo_url}
                          alt="Match"
                          className="w-full h-full object-cover"
                        />
                      ) : (
                        <div className="w-full h-full flex items-center justify-center text-[10px] text-slate-400 font-bold uppercase">
                          No Photo
                        </div>
                      )}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-slate-900 capitalize">
                          {match.breed || match.species}
                        </span>
                        <span className="text-[10px] uppercase font-black px-2 py-0.5 rounded bg-slate-200 text-slate-700">
                          {match.matched_post_type}
                        </span>
                      </div>
                      <div className="text-xs text-slate-500 mt-1">
                        {match.address_text || 'Nearby'} · {match.distance_km} km away
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 w-full sm:w-auto justify-between sm:justify-end">
                    <div className="text-right">
                      <div className="text-xs font-black text-indigo-700">
                        {match.confidence_percent}% Visual Match
                      </div>
                      <div className="text-[10px] text-slate-400">Score: {match.similarity_score}</div>
                    </div>

                    <Link
                      href={`/${locale}/lost-and-found/${match.matched_post_id}`}
                      className="px-3.5 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-lg transition-colors"
                    >
                      Compare
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-slate-400 text-xs">
              No matching listings found within 25 km above the similarity threshold yet.
              We will notify you immediately once a match is submitted!
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
