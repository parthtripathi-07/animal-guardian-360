'use client';

import React, { useState, useEffect } from 'react';
import { MapPin, AlertCircle, RefreshCw, Layers, List } from 'lucide-react';
import { useGeolocation } from '@/hooks/useGeolocation';
import { apiClient } from '@/lib/api-client';
import { NearbyVetsResponse } from '@/types';
import { VetCard } from '@/components/vets/VetCard';
import { SOSModal } from '@/components/vets/SOSModal';

export default function NearbyVetsPage() {
  const { coords, loading: geoLoading, error: geoError, requestLocation } = useGeolocation();
  const [data, setData] = useState<NearbyVetsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [radius, setRadius] = useState(10);
  const [isSOSOpen, setIsSOSOpen] = useState(false);
  const [manualCity, setManualCity] = useState('');

  const fetchVets = async (lat: number, lng: number, r: number) => {
    setLoading(true);
    try {
      const res = await apiClient<NearbyVetsResponse>(`/vets/nearby?lat=${lat}&lng=${lng}&radius=${r}`);
      setData(res);
    } catch (e) {
      console.error('Failed to fetch nearby vets:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (coords) {
      fetchVets(coords.latitude, coords.longitude, radius);
    }
  }, [coords, radius]);

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Top Header & Emergency SOS Banner */}
        <div className="bg-gradient-to-r from-red-600 via-rose-600 to-red-700 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="space-y-1 text-center md:text-left">
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-white/20 text-white uppercase tracking-wider">
              Emergency Services
            </span>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Road Accident Animal SOS
            </h1>
            <p className="text-red-100 text-sm max-w-xl">
              Spotted an injured animal on the road? Tap SOS to alert the 3 nearest emergency veterinary hospitals instantly.
            </p>
          </div>

          <button
            onClick={() => setIsSOSOpen(true)}
            className="w-full md:w-auto px-8 py-3.5 bg-white text-red-600 hover:bg-red-50 font-black rounded-xl text-base shadow-lg transition-transform active:scale-95 shrink-0 flex items-center justify-center gap-2"
          >
            <AlertCircle className="w-5 h-5 animate-pulse" />
            <span>TRIGGER EMERGENCY SOS</span>
          </button>
        </div>

        {/* Filters & Location Bar */}
        <div className="bg-white rounded-xl p-4 border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <MapPin className="w-5 h-5" />
            </div>
            <div>
              <div className="text-xs font-semibold text-slate-500 uppercase">Current Location</div>
              <div className="text-sm font-bold text-slate-800">
                {coords
                  ? `${coords.latitude.toFixed(3)}° N, ${coords.longitude.toFixed(3)}° E`
                  : geoLoading
                  ? 'Detecting GPS...'
                  : 'Location unavailable'}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Radius selector */}
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Radius:</span>
              <select
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="text-xs font-semibold bg-slate-50 border border-slate-200 rounded-lg p-2 outline-none"
              >
                <option value={5}>5 km</option>
                <option value={10}>10 km</option>
                <option value={20}>20 km</option>
                <option value={50}>50 km</option>
              </select>
            </div>

            <button
              onClick={() => coords && fetchVets(coords.latitude, coords.longitude, radius)}
              className="p-2 hover:bg-slate-100 rounded-lg text-slate-600 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>
        </div>

        {/* Hospital Results List */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold text-slate-900">
              Verified Vet Hospitals Nearby ({data?.count || 0})
            </h2>
            {data?.cached && (
              <span className="text-xs text-slate-400">⚡ Cached for fast loading</span>
            )}
          </div>

          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-48 bg-slate-200 animate-pulse rounded-xl" />
              ))}
            </div>
          ) : data && data.vets.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {data.vets.map((hospital) => (
                <VetCard key={hospital.id} hospital={hospital} />
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl p-12 text-center border border-slate-200">
              <MapPin className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-800">No Hospitals Found in this Radius</h3>
              <p className="text-xs text-slate-500 mt-1">Try expanding the search radius to 20 km or 50 km.</p>
            </div>
          )}
        </div>
      </div>

      {/* Road Accident SOS Modal */}
      <SOSModal
        isOpen={isSOSOpen}
        onClose={() => setIsSOSOpen(false)}
        userCoords={coords}
      />
    </div>
  );
}
