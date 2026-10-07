'use client';

import React, { useState } from 'react';
import { AlertTriangle, Camera, MapPin, Phone, CheckCircle, Clock } from 'lucide-react';
import { Coordinates } from '@/hooks/useGeolocation';
import { apiClient } from '@/lib/api-client';
import { AccidentAlert } from '@/types';

interface SOSModalProps {
  isOpen: boolean;
  onClose: () => void;
  userCoords: Coordinates | null;
}

export const SOSModal: React.FC<SOSModalProps> = ({ isOpen, onClose, userCoords }) => {
  const [animalType, setAnimalType] = useState('dog');
  const [condition, setCondition] = useState('');
  const [phone, setPhone] = useState('');
  const [address, setAddress] = useState('');
  const [loading, setLoading] = useState(false);
  const [submittedAlert, setSubmittedAlert] = useState<AccidentAlert | null>(null);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userCoords) {
      setError('GPS Location is required to dispatch emergency rescue');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient<AccidentAlert>('/accidents/sos', {
        method: 'POST',
        body: JSON.stringify({
          animal_type: animalType,
          condition_description: condition,
          latitude: userCoords.latitude,
          longitude: userCoords.longitude,
          address_text: address || 'Auto GPS attached',
          reporter_phone: phone,
        }),
      });
      setSubmittedAlert(response);
    } catch (err: any) {
      setError(err.message || 'Failed to dispatch SOS alert');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-red-100 max-h-[90vh] overflow-y-auto">
        {!submittedAlert ? (
          <>
            <div className="flex items-center gap-3 text-red-600 mb-4">
              <div className="p-3 bg-red-100 rounded-xl">
                <AlertTriangle className="w-8 h-8 animate-pulse text-red-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-slate-900">Road Accident Animal SOS</h2>
                <p className="text-xs text-slate-500">Alerts the 3 nearest veterinary emergency centers</p>
              </div>
            </div>

            {error && (
              <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg mb-4 border border-red-200">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Animal Type
                </label>
                <div className="grid grid-cols-4 gap-2">
                  {['dog', 'cat', 'cow', 'bird'].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => setAnimalType(type)}
                      className={`py-2 text-xs font-medium rounded-lg border capitalize transition-colors ${
                        animalType === type
                          ? 'bg-red-600 text-white border-red-600'
                          : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Condition / Injuries
                </label>
                <textarea
                  rows={2}
                  required
                  placeholder="e.g. Bleeding leg, unable to stand, conscious on road divider"
                  value={condition}
                  onChange={(e) => setCondition(e.target.value)}
                  className="w-full text-sm p-3 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Nearby Landmark or Street
                </label>
                <input
                  type="text"
                  placeholder="e.g. Near Metro Gate 3, Ring Road"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="w-full text-sm p-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold uppercase text-slate-600 mb-1">
                  Your Contact Phone (For Rescue Team)
                </label>
                <input
                  type="tel"
                  required
                  placeholder="e.g. 9876543210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  className="w-full text-sm p-2.5 border border-slate-200 rounded-lg focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>

              {userCoords && (
                <div className="flex items-center text-xs text-emerald-700 bg-emerald-50 p-2.5 rounded-lg">
                  <MapPin className="w-4 h-4 mr-1 text-emerald-600 shrink-0" />
                  GPS Attached: {userCoords.latitude.toFixed(4)}, {userCoords.longitude.toFixed(4)}
                </div>
              )}

              <div className="grid grid-cols-2 gap-3 pt-3">
                <button
                  type="button"
                  onClick={onClose}
                  className="py-2.5 rounded-lg border border-slate-200 text-slate-700 font-medium text-sm hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  className="py-2.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-sm transition-colors shadow-lg shadow-red-500/20 disabled:opacity-50"
                >
                  {loading ? 'Dispatching...' : 'Broadcast SOS Now'}
                </button>
              </div>
            </form>
          </>
        ) : (
          <div className="text-center py-4">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-600">
              <CheckCircle className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-900">SOS Dispatched Successfully!</h3>
            <p className="text-sm text-slate-600 mt-2">
              Alert dispatched to the 3 nearest veterinary hospitals. First hospital to accept locks the case.
            </p>

            <div className="bg-slate-50 p-4 rounded-xl mt-4 text-left border border-slate-200">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                Hospitals Alerted ({submittedAlert.dispatches.length})
              </div>
              <ul className="space-y-2">
                {submittedAlert.dispatches.map((d) => (
                  <li key={d.id} className="flex items-center justify-between text-xs bg-white p-2 rounded border border-slate-100">
                    <span className="font-medium text-slate-800">{d.hospital_name}</span>
                    <span className="text-amber-600 font-semibold bg-amber-50 px-2 py-0.5 rounded">
                      Round {d.escalation_round}: {d.status}
                    </span>
                  </li>
                ))}
              </ul>
              <div className="mt-3 flex items-center text-xs text-slate-500">
                <Clock className="w-3.5 h-3.5 mr-1" /> Escalates automatically to next hospitals if unanswered in 5 mins.
              </div>
            </div>

            <button
              onClick={onClose}
              className="mt-6 w-full py-2.5 rounded-lg bg-slate-900 text-white font-medium text-sm"
            >
              Done & Track Live
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
