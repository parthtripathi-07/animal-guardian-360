'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import {
  ShieldAlert,
  MapPin,
  Camera,
  FileText,
  Phone,
  AlertTriangle,
  CheckCircle,
  Share2,
  Download,
  Info
} from 'lucide-react';
import { useGeolocation } from '@/hooks/useGeolocation';
import { apiClient } from '@/lib/api-client';

export default function CrueltyReportPage() {
  const { coords, loading: geoLoading } = useGeolocation();

  const [category, setCategory] = useState('cruelty');
  const [description, setDescription] = useState('');
  const [address, setAddress] = useState('');
  const [isAnonymous, setIsAnonymous] = useState(false);
  const [dpdpConsent, setDpdpConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);


  const [nearestPolice, setNearestPolice] = useState<any>(null);
  const [submittedReport, setSubmittedReport] = useState<any>(null);

  // Auto-fetch nearest police station on coordinates available
  useEffect(() => {
    if (coords) {
      apiClient(`/reports/police/nearest?lat=${coords.latitude}&lng=${coords.longitude}`)
        .then((data) => setNearestPolice(data))
        .catch(() => {});
    }
  }, [coords]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!coords) {
      setError('Please allow GPS access or provide location coordinates');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const res = await apiClient<any>('/reports', {
        method: 'POST',
        body: JSON.stringify({
          category,
          description,
          latitude: coords.latitude,
          longitude: coords.longitude,
          address_text: address || 'Current GPS coordinates attached',
          is_anonymous: isAnonymous,
          media: [],
        }),
      });
      setSubmittedReport(res);
    } catch (err: any) {
      setError(err.message || 'Failed to submit cruelty report');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 py-10 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-3">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-amber-100 text-amber-700 rounded-xl">
              <ShieldAlert className="w-7 h-7" />
            </div>
            <div>
              <h1 className="text-2xl sm:text-3xl font-black text-slate-900">
                Report Animal Cruelty & Abuse
              </h1>
              <p className="text-xs sm:text-sm text-slate-500">
                Official citizen complaint generator for police and SPCA intervention
              </p>
            </div>
          </div>

          {/* Legal Notice */}
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3 text-xs sm:text-sm text-amber-900">
            <Info className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold">Important Notice:</span> This platform assists in assembling
              verified evidence, identifying the exact police jurisdiction, and preparing an official
              Complaint Summary PDF under Section 11 of the PCA Act 1960 and BNS 325. It does{' '}
              <span className="underline font-bold">NOT</span> automatically register an FIR with the police.
            </div>
          </div>
        </div>

        {/* Form or Result */}
        {!submittedReport ? (
          <form onSubmit={handleSubmit} className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm space-y-6">
            {error && (
              <div className="p-4 bg-red-50 text-red-700 text-sm rounded-xl border border-red-200 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {/* Category Selector */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-2">
                Offence Category
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5">
                {[
                  { id: 'cruelty', label: 'Physical Cruelty' },
                  { id: 'illegal_trade', label: 'Illegal Wildlife Trade' },
                  { id: 'abandonment', label: 'Pet Abandonment' },
                  { id: 'illegal_breeding', label: 'Unlicensed Breeding' },
                  { id: 'other', label: 'Other Abuse' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setCategory(item.id)}
                    className={`py-3 px-3 text-xs font-bold rounded-xl border text-left transition-all ${
                      category === item.id
                        ? 'bg-amber-600 text-white border-amber-600 shadow-sm'
                        : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-2">
                Detailed Incident Description
              </label>
              <textarea
                required
                rows={4}
                minLength={10}
                placeholder="Describe what occurred, species involved, condition of animals, vehicle numbers (if any), and perpetrating individuals..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full text-sm p-3.5 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            {/* Address / Landmark */}
            <div>
              <label className="block text-xs font-bold uppercase text-slate-600 mb-2">
                Street Address or Notable Landmark
              </label>
              <input
                type="text"
                placeholder="e.g. Near Metro Pillar 142, Main Bazaar, Karol Bagh"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                className="w-full text-sm p-3 border border-slate-200 rounded-xl focus:ring-2 focus:ring-amber-500 outline-none"
              />
            </div>

            {/* GPS & Nearest Police Card */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                <div className="text-xs font-bold uppercase text-slate-500 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" /> GPS Tag
                </div>
                <div className="text-sm font-semibold text-slate-800">
                  {coords
                    ? `${coords.latitude.toFixed(4)}° N, ${coords.longitude.toFixed(4)}° E`
                    : geoLoading
                    ? 'Detecting coordinates...'
                    : 'Location required'}
                </div>
              </div>

              {nearestPolice && (
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-1">
                  <div className="text-xs font-bold uppercase text-slate-500 flex items-center gap-1">
                    <ShieldAlert className="w-3.5 h-3.5 text-blue-600" /> Nearest Police
                  </div>
                  <div className="text-xs font-bold text-slate-800 truncate">{nearestPolice.name}</div>
                  <a
                    href="tel:112"
                    className="inline-flex items-center gap-1 text-xs font-black text-red-600 hover:underline pt-0.5"
                  >
                    <Phone className="w-3 h-3" /> Emergency Call 112
                  </a>
                </div>
              )}
            </div>

            {/* Anonymous Toggle */}
            <div className="flex items-center justify-between p-4 bg-slate-50 rounded-xl border border-slate-200">
              <div>
                <div className="text-sm font-bold text-slate-800">Anonymous Whistleblower Mode</div>
                <div className="text-xs text-slate-500">
                  Hides your name and phone from public view and police documents
                </div>
              </div>
              <input
                type="checkbox"
                checked={isAnonymous}
                onChange={(e) => setIsAnonymous(e.target.checked)}
                className="w-5 h-5 accent-amber-600 rounded cursor-pointer"
              />
            </div>

            {/* DPDP Act 2023 Consent Checkbox */}
            <div className="flex items-start gap-3 p-3.5 bg-emerald-50/60 rounded-xl border border-emerald-200/80">
              <input
                type="checkbox"
                id="cruelty-dpdp-consent"
                required
                checked={dpdpConsent}
                onChange={(e) => setDpdpConsent(e.target.checked)}
                className="w-4 h-4 mt-0.5 accent-emerald-600 rounded cursor-pointer"
              />
              <label htmlFor="cruelty-dpdp-consent" className="text-xs text-slate-700 leading-relaxed cursor-pointer">
                I consent to the collection and processing of the submitted incident evidence and location coordinates under the <Link href="/privacy" target="_blank" className="text-emerald-700 underline font-semibold">Digital Personal Data Protection Act, 2023 (DPDP Act)</Link> for statutory animal welfare and law enforcement.
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !dpdpConsent}
              className="w-full py-4 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-black text-sm uppercase tracking-wider shadow-lg shadow-amber-600/20 transition-transform active:scale-95 disabled:opacity-50"
            >
              {loading ? 'Processing & Generating PDF...' : 'Submit Report & Generate PDF'}
            </button>

          </form>
        ) : (
          <div className="bg-white rounded-2xl p-6 sm:p-8 border border-slate-200 shadow-sm text-center space-y-6">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto text-emerald-600">
              <CheckCircle className="w-10 h-10" />
            </div>

            <div>
              <h2 className="text-2xl font-black text-slate-900">Complaint Summary Prepared!</h2>
              <p className="text-sm text-slate-500 mt-1">
                Reference ID: <span className="font-mono font-bold text-slate-800">{submittedReport.id}</span>
              </p>
            </div>

            <div className="bg-slate-50 p-4 rounded-xl text-left border border-slate-200 text-xs sm:text-sm space-y-2">
              <div><span className="font-bold">Designated Police Station:</span> {submittedReport.nearest_police_station?.name}</div>
              <div><span className="font-bold">Emergency Helpline:</span> Call 112</div>
              <div><span className="font-bold">Next Step:</span> Download the formal Form AC-1 summary PDF and submit it to the duty officer / SHO for physical lodging.</div>
            </div>

            {/* Action Buttons */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <a
                href={`http://localhost:8000/api/v1/reports/${submittedReport.id}/pdf`}
                target="_blank"
                rel="noopener noreferrer"
                className="py-3 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm flex items-center justify-center gap-2 shadow-sm"
              >
                <Download className="w-4 h-4" />
                <span>Download Police PDF (AC-1)</span>
              </a>

              <button
                onClick={() => {
                  if (navigator.share) {
                    navigator.share({
                      title: 'Animal Cruelty Incident Complaint',
                      text: submittedReport.shareable_summary,
                    });
                  } else {
                    navigator.clipboard.writeText(submittedReport.shareable_summary);
                    alert('Complaint summary copied to clipboard!');
                  }
                }}
                className="py-3 px-4 rounded-xl border border-slate-300 text-slate-700 font-bold text-sm hover:bg-slate-50 flex items-center justify-center gap-2"
              >
                <Share2 className="w-4 h-4" />
                <span>Share Complaint Text</span>
              </button>
            </div>

            <button
              onClick={() => {
                setSubmittedReport(null);
                setDescription('');
              }}
              className="text-xs text-slate-500 hover:underline pt-2"
            >
              File Another Report
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
