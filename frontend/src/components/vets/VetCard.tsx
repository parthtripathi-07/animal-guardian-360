'use client';

import React from 'react';
import { Phone, Navigation, Clock, ShieldCheck, Ambulance, Star } from 'lucide-react';
import { VetHospital } from '@/types';
import { formatDistance } from '@/lib/utils';

interface VetCardProps {
  hospital: VetHospital;
}

export const VetCard: React.FC<VetCardProps> = ({ hospital }) => {
  const phoneToCall = hospital.emergency_phone || hospital.phone;
  const navigateUrl = `https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col justify-between">
      <div>
        <div className="flex items-start justify-between gap-3">
          <div>
            <h3 className="font-bold text-lg text-slate-900 leading-snug">
              {hospital.name}
            </h3>
            <p className="text-sm text-slate-500 mt-1 line-clamp-2">
              {hospital.address}
            </p>
          </div>
          {hospital.distance_meters !== undefined && (
            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 whitespace-nowrap">
              {formatDistance(hospital.distance_meters)}
            </span>
          )}
        </div>

        {/* Badges */}
        <div className="flex flex-wrap items-center gap-2 mt-3">
          <div className="flex items-center text-xs font-medium text-amber-600 bg-amber-50 px-2 py-0.5 rounded">
            <Star className="w-3.5 h-3.5 fill-amber-500 text-amber-500 mr-1" />
            {hospital.rating.toFixed(1)} ({hospital.total_ratings})
          </div>

          {hospital.is_24x7 && (
            <span className="flex items-center text-xs font-medium text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
              <Clock className="w-3 h-3 mr-1" /> 24x7 Emergency
            </span>
          )}

          {hospital.ambulance_available && (
            <span className="flex items-center text-xs font-medium text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
              <Ambulance className="w-3 h-3 mr-1" /> Pet Ambulance
            </span>
          )}

          {hospital.is_verified && (
            <span className="flex items-center text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
              <ShieldCheck className="w-3 h-3 mr-1" /> Verified
            </span>
          )}
        </div>
      </div>

      {/* Action Buttons: Call & Navigate */}
      <div className="grid grid-cols-2 gap-3 mt-5 pt-4 border-t border-slate-100">
        <a
          href={`tel:${phoneToCall}`}
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-medium text-sm transition-colors shadow-sm"
        >
          <Phone className="w-4 h-4" />
          <span>Call</span>
        </a>

        <a
          href={navigateUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-800 font-medium text-sm transition-colors"
        >
          <Navigation className="w-4 h-4 text-slate-600" />
          <span>Navigate</span>
        </a>
      </div>
    </div>
  );
};
