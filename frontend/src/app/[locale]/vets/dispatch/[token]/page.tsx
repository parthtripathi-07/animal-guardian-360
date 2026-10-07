'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { AlertCircle, CheckCircle, XCircle, MapPin, Clock, Phone, Navigation } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export default function HospitalDispatchActionPage() {
  const params = useParams();
  const token = params?.token as string;
  const router = useRouter();

  const [details, setDetails] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [eta, setEta] = useState(15);
  const [resultMsg, setResultMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    if (!token) return;
    apiClient(`/accidents/dispatch/${token}`)
      .then((data) => setDetails(data))
      .catch((err) => {
        setResultMsg({ type: 'error', text: err.message || 'Invalid or expired dispatch token' });
      })
      .finally(() => setLoading(false));
  }, [token]);

  const handleAction = async (action: 'accept' | 'decline') => {
    setActionLoading(true);
    setResultMsg(null);
    try {
      const res = await apiClient<any>(`/accidents/dispatch/${token}/action`, {
        method: 'POST',
        body: JSON.stringify({
          action,
          eta_minutes: eta,
          decline_reason: action === 'decline' ? 'Capacity full or specialist unavailable' : undefined,
        }),
      });
      setResultMsg({ type: 'success', text: res.message });
      // Reload details to show updated status
      setDetails((prev: any) => ({
        ...prev,
        dispatch_status: action === 'accept' ? 'accepted' : 'declined',
      }));
    } catch (err: any) {
      setResultMsg({ type: 'error', text: err.message || 'Action failed' });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-12 w-12 border-4 border-red-600 border-t-transparent" />
      </div>
    );
  }

  const alert = details?.alert;
  const isPending = details?.dispatch_status === 'pending';

  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4 sm:px-6">
      <div className="max-w-xl mx-auto bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        {/* Banner */}
        <div className="bg-red-600 p-6 text-white text-center">
          <div className="w-12 h-12 bg-white/20 rounded-full flex items-center justify-center mx-auto mb-2">
            <AlertCircle className="w-8 h-8 text-white animate-pulse" />
          </div>
          <h1 className="text-2xl font-black">EMERGENCY ROAD ACCIDENT SOS</h1>
          <p className="text-red-100 text-xs mt-1">Dispatched to: {details?.hospital_name}</p>
        </div>

        <div className="p-6 space-y-6">
          {resultMsg && (
            <div
              className={`p-4 rounded-xl flex items-center gap-3 text-sm font-medium ${
                resultMsg.type === 'success'
                  ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                  : 'bg-red-50 text-red-800 border border-red-200'
              }`}
            >
              {resultMsg.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              ) : (
                <XCircle className="w-5 h-5 text-red-600 shrink-0" />
              )}
              <span>{resultMsg.text}</span>
            </div>
          )}

          {alert && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3 text-sm">
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Animal</div>
                  <div className="font-bold text-slate-800 capitalize mt-0.5">{alert.animal_type}</div>
                </div>
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                  <div className="text-xs text-slate-500 font-semibold uppercase">Reported At</div>
                  <div className="font-bold text-slate-800 mt-0.5">
                    {new Date(alert.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                <div className="text-xs text-slate-500 font-semibold uppercase">Condition / Notes</div>
                <p className="text-sm text-slate-800 mt-1 font-medium">
                  {alert.condition_description || 'No additional notes provided'}
                </p>
              </div>

              <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-100 space-y-2">
                <div className="flex items-center text-xs text-slate-500 font-semibold uppercase">
                  <MapPin className="w-4 h-4 mr-1 text-red-600" /> Location
                </div>
                <p className="text-sm text-slate-800 font-medium">{alert.address_text}</p>
                <a
                  href={`https://www.google.com/maps/dir/?api=1&destination=${alert.latitude},${alert.longitude}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center text-xs text-blue-600 font-semibold hover:underline"
                >
                  <Navigation className="w-3.5 h-3.5 mr-1" /> Open Live Navigation
                </a>
              </div>

              {alert.reporter_phone && (
                <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-100 text-sm">
                  <span className="text-slate-600">Reporter Contact:</span>
                  <a
                    href={`tel:${alert.reporter_phone}`}
                    className="flex items-center font-bold text-emerald-600 hover:underline"
                  >
                    <Phone className="w-4 h-4 mr-1" /> {alert.reporter_phone}
                  </a>
                </div>
              )}
            </div>
          )}

          {isPending ? (
            <div className="space-y-4 pt-4 border-t border-slate-200">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase mb-2">
                  Estimated Arrival Time (ETA in minutes)
                </label>
                <div className="flex items-center gap-3">
                  {[10, 15, 25, 40].map((mins) => (
                    <button
                      key={mins}
                      type="button"
                      onClick={() => setEta(mins)}
                      className={`flex-1 py-2 text-xs font-bold rounded-lg border transition-all ${
                        eta === mins
                          ? 'bg-emerald-600 text-white border-emerald-600'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                      }`}
                    >
                      {mins} mins
                    </button>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleAction('decline')}
                  className="py-3 px-4 rounded-xl border border-slate-300 text-slate-700 font-bold text-sm hover:bg-slate-100 transition-colors disabled:opacity-50"
                >
                  Decline Case
                </button>

                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleAction('accept')}
                  className="py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-extrabold text-sm shadow-lg shadow-emerald-600/30 transition-transform active:scale-95 disabled:opacity-50"
                >
                  {actionLoading ? 'Locking...' : 'ACCEPT & DISPATCH'}
                </button>
              </div>
            </div>
          ) : (
            <div className="p-4 bg-slate-100 text-slate-700 text-center rounded-xl font-bold text-sm">
              Status: Case marked as {details?.dispatch_status?.toUpperCase()}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
