'use client';

import React, { useState, useEffect } from 'react';
import { AlertTriangle, Clock, CheckCircle, Phone, Navigation, RefreshCw } from 'lucide-react';
import { apiClient } from '@/lib/api-client';
import { AccidentAlert } from '@/types';

export default function HospitalDashboardPage() {
  const [alerts, setAlerts] = useState<AccidentAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'accepted' | 'reached'>('all');

  const fetchDashboardAlerts = async () => {
    setLoading(true);
    try {
      const data = await apiClient<AccidentAlert[]>('/accidents/hospital/dashboard');
      setAlerts(data);
    } catch (e) {
      console.error('Failed to load hospital dashboard:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardAlerts();
  }, []);

  const updateStatus = async (alertId: string, status: 'reached' | 'closed') => {
    try {
      await apiClient(`/accidents/${alertId}/status`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      fetchDashboardAlerts();
    } catch (e: any) {
      alert(e.message || 'Failed to update status');
    }
  };

  const filteredAlerts = alerts.filter((a) => {
    if (filter === 'all') return true;
    return a.status === filter;
  });

  return (
    <div className="min-h-screen bg-slate-50 py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div>
            <h1 className="text-2xl font-black text-slate-900">Hospital Emergency Dispatch Board</h1>
            <p className="text-sm text-slate-500">Live incoming road accident cases and rescue tracking</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchDashboardAlerts}
              className="flex items-center gap-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg transition-colors"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              <span>Refresh Board</span>
            </button>
          </div>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 border-b border-slate-200 pb-2">
          {(['all', 'accepted', 'reached'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-4 py-2 text-xs font-bold rounded-lg capitalize transition-colors ${
                filter === tab
                  ? 'bg-slate-900 text-white'
                  : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
              }`}
            >
              {tab === 'all' ? 'All Active Cases' : tab}
            </button>
          ))}
        </div>

        {/* Cases List */}
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading live alerts...</div>
        ) : filteredAlerts.length === 0 ? (
          <div className="bg-white rounded-2xl p-12 text-center border border-slate-200">
            <CheckCircle className="w-12 h-12 text-emerald-500 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-800">No Pending Emergency Cases</h3>
            <p className="text-xs text-slate-500 mt-1">All dispatched accidents are currently addressed or closed.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {filteredAlerts.map((item) => (
              <div
                key={item.id}
                className="bg-white rounded-xl border border-slate-200 shadow-sm p-5 space-y-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-bold capitalize bg-red-50 text-red-700">
                      <AlertTriangle className="w-3.5 h-3.5 mr-1 text-red-600" />
                      {item.animal_type}
                    </span>
                    <span
                      className={`text-xs font-extrabold uppercase px-2.5 py-1 rounded-full ${
                        item.status === 'accepted'
                          ? 'bg-amber-100 text-amber-800'
                          : item.status === 'reached'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <p className="text-sm text-slate-800 font-medium mt-3">
                    {item.condition_description || 'Injured animal reported via SOS'}
                  </p>

                  <div className="text-xs text-slate-500 mt-2 space-y-1">
                    <div>Location: {item.address_text}</div>
                    {item.eta_minutes && (
                      <div className="flex items-center text-amber-700 font-semibold">
                        <Clock className="w-3.5 h-3.5 mr-1" /> Hospital ETA: {item.eta_minutes} mins
                      </div>
                    )}
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 space-y-3">
                  <div className="flex items-center justify-between text-xs">
                    {item.reporter_phone && (
                      <a
                        href={`tel:${item.reporter_phone}`}
                        className="flex items-center font-bold text-emerald-600 hover:underline"
                      >
                        <Phone className="w-3.5 h-3.5 mr-1" /> Call Reporter ({item.reporter_phone})
                      </a>
                    )}
                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${item.latitude},${item.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center font-bold text-blue-600 hover:underline"
                    >
                      <Navigation className="w-3.5 h-3.5 mr-1" /> Directions
                    </a>
                  </div>

                  {/* Status Progression Buttons */}
                  <div className="flex items-center gap-2">
                    {item.status === 'accepted' && (
                      <button
                        onClick={() => updateStatus(item.id, 'reached')}
                        className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-lg transition-colors"
                      >
                        Mark Ambulance Reached
                      </button>
                    )}
                    {item.status === 'reached' && (
                      <button
                        onClick={() => updateStatus(item.id, 'closed')}
                        className="w-full py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg transition-colors"
                      >
                        Mark Case Closed / Admitted
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
