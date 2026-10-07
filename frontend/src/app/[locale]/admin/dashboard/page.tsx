'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Shield, 
  BarChart3, 
  AlertTriangle, 
  CheckCircle2, 
  Building2, 
  FileText, 
  DollarSign, 
  History, 
  Eye, 
  Ban, 
  RotateCcw, 
  Plus, 
  ExternalLink,
  Users,
  Search,
  Filter
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface AdminStats {
  total_users: number;
  total_hospitals: number;
  pending_hospitals: number;
  total_accidents: number;
  active_accidents: number;
  total_cruelty_reports: number;
  pending_reports: number;
  total_lost_found_posts: number;
  reunited_pets: number;
  total_donations_raised_inr: number;
  total_funds_allocated_inr: number;
  active_strikes_count: number;
}

interface CrueltyReport {
  id: string;
  category: string;
  description: string;
  latitude: number;
  longitude: number;
  status: string;
  created_at: string;
  media: Array<{ file_url: string; media_type: string }>;
}

interface Hospital {
  id: string;
  name: string;
  phone: string;
  address: string;
  is_verified: boolean;
  rating: number;
}

interface Strike {
  id: string;
  user_id: string;
  user_phone?: string;
  user_email?: string;
  strike_number: number;
  reason: string;
  created_at: string;
}

interface AuditLog {
  id: string;
  actor_email?: string;
  action: string;
  entity_name: string;
  entity_id?: string;
  details?: any;
  created_at: string;
}

export default function AdminDashboardPage() {
  const [activeTab, setActiveTab] = useState<
    'overview' | 'reports' | 'hospitals' | 'strikes' | 'finances' | 'audit'
  >('overview');

  const [stats, setStats] = useState<AdminStats | null>(null);
  const [reports, setReports] = useState<CrueltyReport[]>([]);
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [strikes, setStrikes] = useState<Strike[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionMsg, setActionMsg] = useState<string | null>(null);
  const [isAdminAuthed, setIsAdminAuthed] = useState<boolean>(true);

  // Financial allocation modal state
  const [allocCategory, setAllocCategory] = useState<string>('rescue_ops');
  const [allocTitle, setAllocTitle] = useState<string>('');
  const [allocDesc, setAllocDesc] = useState<string>('');
  const [allocAmount, setAllocAmount] = useState<string>('');
  const [allocDate, setAllocDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [allocReceipt, setAllocReceipt] = useState<string>('');

  useEffect(() => {
    loadData();
  }, [activeTab]);

  const loadData = async () => {
    setLoading(true);
    setActionMsg(null);
    try {
      if (activeTab === 'overview') {
        const res = await apiClient<AdminStats>('/admin/stats');
        setStats(res);
      } else if (activeTab === 'reports') {
        const res = await apiClient<CrueltyReport[]>('/reports/admin/queue');
        setReports(res);
      } else if (activeTab === 'hospitals') {
        const res = await apiClient<Hospital[]>('/admin/hospitals');
        setHospitals(res);
      } else if (activeTab === 'strikes') {
        const res = await apiClient<Strike[]>('/admin/strikes');
        setStrikes(res);
      } else if (activeTab === 'audit') {
        const res = await apiClient<AuditLog[]>('/admin/audit-logs');
        setAuditLogs(res);
      }
      setIsAdminAuthed(true);
    } catch (e: any) {
      console.warn('Admin load error:', e);
      if (e?.status === 401 || e?.status === 403 || e?.message?.includes('credentials')) {
        setIsAdminAuthed(false);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAdminLogin = async () => {
    setLoading(true);
    try {
      const sendRes: any = await apiClient('/auth/otp/send', {
        method: 'POST',
        body: JSON.stringify({ identifier: '+919999999999', purpose: 'login' }),
      });
      const otp = sendRes.dev_otp || '123456';
      const verifyRes: any = await apiClient('/auth/otp/verify', {
        method: 'POST',
        body: JSON.stringify({ identifier: '+919999999999', code: otp, purpose: 'login' }),
      });
      if (verifyRes.access_token) {
        localStorage.setItem('access_token', verifyRes.access_token);
        setIsAdminAuthed(true);
        setActionMsg('Logged in as Super Admin (+919999999999)');
        loadData();
      }
    } catch (err: any) {
      setActionMsg(`Admin login error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    setIsAdminAuthed(false);
    setStats(null);
    setActionMsg('Logged out of Admin Session.');
  };

  const handleReviewReport = async (reportId: string, action: 'verified' | 'fake', notes: string) => {
    try {
      await apiClient(`/reports/admin/${reportId}/review`, {
        method: 'POST',
        body: JSON.stringify({ action, notes }),
      });
      setActionMsg(`Report marked as ${action}. Strike updated accordingly.`);
      loadData();
    } catch (e: any) {
      setActionMsg(`Failed to review report: ${e.message}`);
    }
  };

  const handleVerifyHospital = async (hospitalId: string, isVerified: boolean) => {
    try {
      await apiClient(`/admin/hospitals/${hospitalId}/verify`, {
        method: 'PATCH',
        body: JSON.stringify({ is_verified: isVerified, notes: 'Admin verification updated' }),
      });
      setActionMsg(`Hospital status updated to ${isVerified ? 'Verified' : 'Unverified'}.`);
      loadData();
    } catch (e: any) {
      setActionMsg(`Failed to update hospital: ${e.message}`);
    }
  };

  const handleRevokeStrike = async (strikeId: string) => {
    try {
      await apiClient(`/admin/strikes/${strikeId}`, { method: 'DELETE' });
      setActionMsg('Strike revoked and user penalties re-evaluated.');
      loadData();
    } catch (e: any) {
      setActionMsg(`Failed to revoke strike: ${e.message}`);
    }
  };

  const handleCreateAllocation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiClient('/donations/allocations', {
        method: 'POST',
        body: JSON.stringify({
          category: allocCategory,
          title: allocTitle,
          description: allocDesc || null,
          amount_inr: parseFloat(allocAmount),
          allocation_date: allocDate,
          receipt_url: allocReceipt || null,
        }),
      });
      setActionMsg('Audited expenditure allocation published to Transparency Ledger.');
      setAllocTitle('');
      setAllocDesc('');
      setAllocAmount('');
      setAllocReceipt('');
    } catch (e: any) {
      setActionMsg(`Failed to record allocation: ${e.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-gray-200 dark:border-gray-800 gap-4">
        <div>
          <div className="flex items-center gap-2 text-rose-600 font-semibold text-xs tracking-wider uppercase">
            <Shield className="w-4 h-4" />
            <span>High-Privilege Operations</span>
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mt-1">
            Animal Guardian 360° Admin Console
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">
            Real-time incident dispatch, anti-abuse strike management, hospital verification, and financial oversight.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isAdminAuthed ? (
            <button
              onClick={handleLogout}
              className="px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-lg border border-slate-300 flex items-center gap-1.5 transition-colors"
            >
              <span>Logout Admin</span>
            </button>
          ) : (
            <button
              onClick={handleQuickAdminLogin}
              className="px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-lg shadow-sm flex items-center gap-1.5 transition-colors"
            >
              <Shield className="w-3.5 h-3.5" />
              <span>1-Click Admin Login</span>
            </button>
          )}

          <Link
            href="/donate/transparency"
            target="_blank"
            className="px-3 py-2 bg-emerald-50 text-emerald-700 text-xs font-bold rounded-lg border border-emerald-200 flex items-center gap-1.5"
          >
            <span>Public Ledger</span>
            <ExternalLink className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>

      {actionMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-sm font-medium flex items-center justify-between">
          <span>{actionMsg}</span>
          <button onClick={() => setActionMsg(null)} className="text-xs font-bold uppercase underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Tab Navigation */}
      <div className="flex overflow-x-auto space-x-2 border-b border-gray-200 dark:border-gray-800 pb-2">
        {[
          { key: 'overview', label: 'Overview & KPIs', icon: BarChart3 },
          { key: 'reports', label: 'Cruelty Review Queue', icon: AlertTriangle },
          { key: 'hospitals', label: 'Hospital Verification', icon: Building2 },
          { key: 'strikes', label: 'Anti-Abuse Strikes', icon: Ban },
          { key: 'finances', label: 'Record Expenditure', icon: DollarSign },
          { key: 'audit', label: 'Audit Trail', icon: History },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key as any)}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold transition-all whitespace-nowrap ${
                isActive
                  ? 'bg-emerald-600 text-white shadow-sm'
                  : 'bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {loading && (
        <div className="text-center py-16 text-gray-500 animate-pulse text-sm">
          Loading administration console data...
        </div>
      )}

      {!loading && !isAdminAuthed && (
        <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-2xl p-8 text-center space-y-4 max-w-lg mx-auto my-8 shadow-sm">
          <div className="w-14 h-14 bg-amber-100 text-amber-700 rounded-2xl flex items-center justify-center mx-auto shadow-sm">
            <Shield className="w-7 h-7" />
          </div>
          <h2 className="text-xl font-bold text-slate-900 dark:text-white">Admin Privileges Required</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            You need to be authenticated as an Administrator to view KPIs, review animal abuse reports, verify hospitals, and manage funds.
          </p>
          <button
            onClick={handleQuickAdminLogin}
            className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-sm rounded-xl shadow-md transition-all flex items-center gap-2 mx-auto"
          >
            <Shield className="w-4 h-4" />
            <span>1-Click Login as Admin (+91 99999 99999)</span>
          </button>
        </div>
      )}

      {!loading && isAdminAuthed && activeTab === 'overview' && stats && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Total Registered Users</span>
              <div className="text-3xl font-extrabold text-gray-900 dark:text-white mt-1">
                {stats.total_users}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Hospitals (Pending / Total)</span>
              <div className="text-3xl font-extrabold text-amber-600 mt-1">
                {stats.pending_hospitals} / {stats.total_hospitals}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Accident Dispatches (Active)</span>
              <div className="text-3xl font-extrabold text-rose-600 mt-1">
                {stats.active_accidents} / {stats.total_accidents}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Cruelty Reports (Pending)</span>
              <div className="text-3xl font-extrabold text-indigo-600 mt-1">
                {stats.pending_reports} / {stats.total_cruelty_reports}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Reunited Pets</span>
              <div className="text-3xl font-extrabold text-emerald-600 mt-1">
                {stats.reunited_pets} / {stats.total_lost_found_posts}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Total Donations Raised</span>
              <div className="text-3xl font-extrabold text-emerald-600 mt-1">
                ₹{stats.total_donations_raised_inr.toLocaleString('en-IN')}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Total Funds Allocated</span>
              <div className="text-3xl font-extrabold text-gray-900 dark:text-white mt-1">
                ₹{stats.total_funds_allocated_inr.toLocaleString('en-IN')}
              </div>
            </div>

            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl border border-gray-200 dark:border-gray-800 shadow-sm">
              <span className="text-xs uppercase font-bold text-gray-400">Active Strikes Issued</span>
              <div className="text-3xl font-extrabold text-red-600 mt-1">
                {stats.active_strikes_count}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Cruelty Queue Tab */}
      {!loading && activeTab === 'reports' && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Cruelty Reports Moderation Queue ({reports.length})
          </h2>

          {reports.length === 0 ? (
            <div className="p-8 text-center text-gray-400 bg-white rounded-2xl border">
              No pending cruelty reports in queue.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {reports.map((r) => (
                <div key={r.id} className="bg-white p-5 rounded-2xl border space-y-3">
                  <div className="flex justify-between items-start">
                    <span className="text-xs font-bold uppercase bg-red-100 text-red-800 px-2 py-0.5 rounded-md">
                      {r.category}
                    </span>
                    <span className="text-xs font-mono text-gray-400">
                      {new Date(r.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <p className="text-xs text-gray-700 font-medium">{r.description}</p>

                  <div className="text-[11px] text-gray-500 font-mono">
                    GPS: {r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}
                  </div>

                  <div className="flex items-center gap-2 pt-2 border-t">
                    <button
                      onClick={() => handleReviewReport(r.id, 'verified', 'Report verified by field officer')}
                      className="flex-1 py-1.5 px-3 bg-emerald-600 text-white rounded-lg text-xs font-bold hover:bg-emerald-700"
                    >
                      Approve & Dispatch
                    </button>
                    <button
                      onClick={() => handleReviewReport(r.id, 'fake', 'Fake submission with invalid evidence')}
                      className="flex-1 py-1.5 px-3 bg-red-600 text-white rounded-lg text-xs font-bold hover:bg-red-700"
                    >
                      Mark Fake (Strike)
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Hospital Verification Tab */}
      {!loading && activeTab === 'hospitals' && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Veterinary Hospitals & Shelters ({hospitals.length})
          </h2>

          <div className="bg-white rounded-2xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 font-bold border-b text-gray-500 uppercase">
                <tr>
                  <th className="py-3 px-4">Hospital Name</th>
                  <th className="py-3 px-4">Phone</th>
                  <th className="py-3 px-4">Address</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y text-gray-700">
                {hospitals.map((h) => (
                  <tr key={h.id}>
                    <td className="py-3 px-4 font-bold">{h.name}</td>
                    <td className="py-3 px-4">{h.phone}</td>
                    <td className="py-3 px-4">{h.address}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                        h.is_verified ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {h.is_verified ? 'Verified' : 'Pending Verification'}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <button
                        onClick={() => handleVerifyHospital(h.id, !h.is_verified)}
                        className={`px-3 py-1 rounded-lg font-bold text-[11px] ${
                          h.is_verified ? 'bg-gray-100 text-gray-600 hover:bg-gray-200' : 'bg-emerald-600 text-white hover:bg-emerald-700'
                        }`}
                      >
                        {h.is_verified ? 'Unverify' : 'Verify Hospital'}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Strikes Tab */}
      {!loading && activeTab === 'strikes' && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Anti-Abuse Strikes & Suspended Reporters ({strikes.length})
          </h2>

          <div className="bg-white rounded-2xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 font-bold border-b text-gray-500 uppercase">
                <tr>
                  <th className="py-3 px-4">User</th>
                  <th className="py-3 px-4">Strike Level</th>
                  <th className="py-3 px-4">Reason</th>
                  <th className="py-3 px-4">Date</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y text-gray-700">
                {strikes.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-gray-400">
                      Zero community strikes recorded.
                    </td>
                  </tr>
                ) : (
                  strikes.map((s) => (
                    <tr key={s.id}>
                      <td className="py-3 px-4 font-mono">{s.user_phone || s.user_email || s.user_id}</td>
                      <td className="py-3 px-4">
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-rose-100 text-rose-800">
                          Strike #{s.strike_number}
                        </span>
                      </td>
                      <td className="py-3 px-4">{s.reason}</td>
                      <td className="py-3 px-4 text-gray-400 font-mono">
                        {new Date(s.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <button
                          onClick={() => handleRevokeStrike(s.id)}
                          className="px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-lg font-bold text-[11px] hover:bg-red-100 flex items-center gap-1 mx-auto"
                        >
                          <RotateCcw className="w-3 h-3" />
                          <span>Revoke Strike</span>
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Finances Tab */}
      {!loading && activeTab === 'finances' && (
        <div className="max-w-2xl bg-white p-6 rounded-2xl border space-y-4">
          <h2 className="text-lg font-bold text-gray-900">Record Audited Expenditure Allocation</h2>
          <p className="text-xs text-gray-500">
            Every entry added here appears instantly on the public transparency ledger with verified receipts.
          </p>

          <form onSubmit={handleCreateAllocation} className="space-y-4">
            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Expenditure Category</label>
              <select
                value={allocCategory}
                onChange={(e) => setAllocCategory(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border text-sm"
              >
                <option value="rescue_ops">Rescue & Emergency Operations</option>
                <option value="medical_supplies">Veterinary Medicines & Kits</option>
                <option value="food_feeding">Stray Feeding & Nutrition</option>
                <option value="shelters">Shelter Maintenance & Care</option>
                <option value="infrastructure">Equipment & Ambulances</option>
                <option value="admin">Operations & Auditing</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Expenditure Title / Purpose *</label>
              <input
                type="text"
                required
                placeholder="e.g. 50 Anti-rabies vaccine vials"
                value={allocTitle}
                onChange={(e) => setAllocTitle(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border text-sm"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Amount (INR) *</label>
                <input
                  type="number"
                  min="1"
                  required
                  placeholder="e.g. 12500"
                  value={allocAmount}
                  onChange={(e) => setAllocAmount(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Allocation Date *</label>
                <input
                  type="date"
                  required
                  value={allocDate}
                  onChange={(e) => setAllocDate(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-gray-700 mb-1">Public Receipt / Invoice URL</label>
              <input
                type="url"
                placeholder="https://storage.animalguardian360.org/receipts/inv-2026-99.pdf"
                value={allocReceipt}
                onChange={(e) => setAllocReceipt(e.target.value)}
                className="w-full px-3 py-2 rounded-xl border text-sm"
              />
            </div>

            <button
              type="submit"
              className="w-full py-3 bg-emerald-600 text-white rounded-xl font-bold text-sm hover:bg-emerald-700"
            >
              Publish Expenditure to Public Ledger
            </button>
          </form>
        </div>
      )}

      {/* Audit Log Tab */}
      {!loading && activeTab === 'audit' && (
        <div className="space-y-4">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">
            Immutable Audit Trail ({auditLogs.length})
          </h2>

          <div className="bg-white rounded-2xl border overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-gray-50 font-bold border-b text-gray-500 uppercase">
                <tr>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Entity</th>
                  <th className="py-3 px-4">Officer / Actor</th>
                  <th className="py-3 px-4">Details</th>
                  <th className="py-3 px-4 font-mono">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y text-gray-700">
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-6 text-center text-gray-400">
                      No administrative audit entries logged yet.
                    </td>
                  </tr>
                ) : (
                  auditLogs.map((l) => (
                    <tr key={l.id}>
                      <td className="py-3 px-4 font-bold text-emerald-700">{l.action}</td>
                      <td className="py-3 px-4">{l.entity_name}</td>
                      <td className="py-3 px-4 font-mono">{l.actor_email || 'System'}</td>
                      <td className="py-3 px-4 font-mono text-[11px] max-w-xs truncate">
                        {JSON.stringify(l.details)}
                      </td>
                      <td className="py-3 px-4 font-mono text-gray-400">
                        {new Date(l.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
