'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Heart, 
  ShieldCheck, 
  Receipt, 
  QrCode, 
  CreditCard, 
  CheckCircle2, 
  AlertCircle, 
  Download, 
  ArrowRight,
  TrendingUp,
  Sparkles
} from 'lucide-react';
import { apiClient } from '@/lib/api-client';

interface Campaign {
  id: string;
  title: string;
  description: string;
  target_amount_inr: number;
  raised_amount_inr: number;
  progress_percent: number;
}

export default function DonatePage() {
  const [amount, setAmount] = useState<number>(1000);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [donorName, setDonorName] = useState<string>('');
  const [donorEmail, setDonorEmail] = useState<string>('');
  const [donorPhone, setDonorPhone] = useState<string>('');
  const [donorPan, setDonorPan] = useState<string>('');
  const [donorAddress, setDonorAddress] = useState<string>('');
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>('');
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);

  const [loading, setLoading] = useState<boolean>(false);
  const [dpdpConsent, setDpdpConsent] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  
  // Checkout & Completion State
  const [paymentStep, setPaymentStep] = useState<'form' | 'qr_mock' | 'completed'>('form');
  const [currentOrder, setCurrentOrder] = useState<any>(null);
  const [verifiedDonation, setVerifiedDonation] = useState<any>(null);

  const PRESET_AMOUNTS = [500, 1000, 2500, 5000];

  useEffect(() => {
    async function loadCampaigns() {
      try {
        const data = await apiClient<Campaign[]>('/donations/campaigns');
        setCampaigns(data);
      } catch (e) {
        console.warn('Could not load campaigns:', e);
      }
    }
    loadCampaigns();
  }, []);

  const handlePresetSelect = (val: number) => {
    setAmount(val);
    setCustomAmount('');
  };

  const handleCustomChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setCustomAmount(val);
    const num = parseFloat(val);
    if (!isNaN(num) && num > 0) {
      setAmount(num);
    }
  };

  const validatePan = (pan: string) => {
    if (!pan) return true;
    return /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(pan.toUpperCase());
  };

  const handleInitiateDonation = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);

    if (amount < 10) {
      setErrorMsg('Minimum donation amount is ₹10.');
      return;
    }
    if (!donorName.trim() || !donorEmail.trim()) {
      setErrorMsg('Please enter your name and email address to receive your 80G receipt.');
      return;
    }
    if (donorPan.trim() && !validatePan(donorPan)) {
      setErrorMsg('Please enter a valid 10-character Indian PAN (e.g. ABCDE1234F) for Section 80G tax benefits.');
      return;
    }

    try {
      setLoading(true);
      const payload = {
        amount_inr: amount,
        donor_name: donorName.trim(),
        donor_email: donorEmail.trim(),
        donor_phone: donorPhone.trim() || null,
        donor_pan: donorPan.trim() ? donorPan.trim().toUpperCase() : null,
        donor_address: donorAddress.trim() || null,
        campaign_id: selectedCampaignId || null,
      };

      const orderData = await apiClient<any>('/donations/orders', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setCurrentOrder(orderData);
      setPaymentStep('qr_mock');
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to initialize payment gateway.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulatePaymentSuccess = async () => {
    if (!currentOrder) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const verifyPayload = {
        razorpay_order_id: currentOrder.order_id,
        razorpay_payment_id: `pay_mock_${Date.now()}`,
        razorpay_signature: 'mock_valid_signature',
      };

      const donationData = await apiClient<any>('/donations/verify', {
        method: 'POST',
        body: JSON.stringify(verifyPayload),
      });

      setVerifiedDonation(donationData);
      setPaymentStep('completed');
    } catch (err: any) {
      setErrorMsg(err.message || 'Signature verification failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadReceipt = () => {
    if (!verifiedDonation?.id) return;
    const downloadUrl = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'}/donations/${verifiedDonation.id}/receipt`;
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Top Banner & Transparency Link */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-6 border-b border-gray-200 dark:border-gray-800 mb-8 gap-4">
        <div>
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-semibold text-sm">
            <Heart className="w-4 h-4 fill-current" />
            <span>100% Tax Deductible (Section 80G)</span>
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 dark:text-white mt-1">
            Empower Rescues, Heal Lives
          </h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
            Every rupee directly finances veterinary trauma surgery, ambulances, shelter feeding, and critical supplies.
          </p>
        </div>

        <Link
          href="/donate/transparency"
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-lg text-sm font-medium hover:bg-emerald-100 transition-colors border border-emerald-200 dark:border-emerald-800"
        >
          <TrendingUp className="w-4 h-4" />
          <span>Public Transparency Ledger</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>

      {paymentStep === 'form' && (
        <form onSubmit={handleInitiateDonation} className="space-y-8">
          {errorMsg && (
            <div className="p-4 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl flex items-start gap-3 text-red-700 dark:text-red-300 text-sm">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Amount Selection */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 space-y-4">
            <label className="block text-base font-bold text-gray-900 dark:text-white">
              1. Choose Donation Amount (INR)
            </label>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {PRESET_AMOUNTS.map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => handlePresetSelect(val)}
                  className={`py-3 px-4 rounded-xl font-bold text-lg border transition-all ${
                    amount === val && !customAmount
                      ? 'bg-emerald-600 text-white border-emerald-600 shadow-md ring-2 ring-emerald-500/20'
                      : 'bg-gray-50 dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-700 hover:bg-gray-100'
                  }`}
                >
                  ₹{val.toLocaleString('en-IN')}
                </button>
              ))}
            </div>

            <div className="pt-2">
              <label className="text-xs text-gray-500 uppercase tracking-wide font-semibold block mb-1">
                Or enter custom amount (₹)
              </label>
              <div className="relative">
                <span className="absolute left-3.5 top-2.5 text-gray-500 font-bold">₹</span>
                <input
                  type="number"
                  min="10"
                  step="10"
                  placeholder="e.g. 1500"
                  value={customAmount}
                  onChange={handleCustomChange}
                  className="w-full pl-8 pr-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Campaign allocation */}
          {campaigns.length > 0 && (
            <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 space-y-3">
              <label className="block text-base font-bold text-gray-900 dark:text-white">
                2. Select Cause / Campaign (Optional)
              </label>
              <select
                value={selectedCampaignId}
                onChange={(e) => setSelectedCampaignId(e.target.value)}
                className="w-full px-4 py-2.5 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                <option value="">General Animal Welfare & Emergency Fund</option>
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.title} (Target: ₹{c.target_amount_inr.toLocaleString('en-IN')})
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* 80G Tax Exemption & Donor Info */}
          <div className="bg-white dark:bg-gray-900 p-6 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-800 space-y-4">
            <div className="flex items-center justify-between">
              <label className="block text-base font-bold text-gray-900 dark:text-white">
                3. Donor Information & 80G Tax Exemption Receipt
              </label>
              <span className="inline-flex items-center gap-1 text-xs px-2.5 py-1 bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 rounded-full font-medium">
                <ShieldCheck className="w-3.5 h-3.5" /> 80G Benefit
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Full Name (as per PAN) *
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Ramesh Kumar"
                  value={donorName}
                  onChange={(e) => setDonorName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Email Address (Receipt will be sent here) *
                </label>
                <input
                  type="email"
                  required
                  placeholder="e.g. ramesh@example.com"
                  value={donorEmail}
                  onChange={(e) => setDonorEmail(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Indian PAN (Required for Section 80G Tax Exemption)
                </label>
                <input
                  type="text"
                  maxLength={10}
                  placeholder="e.g. ABCDE1234F"
                  value={donorPan}
                  onChange={(e) => setDonorPan(e.target.value.toUpperCase())}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white uppercase focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm font-mono"
                />
                <span className="text-[11px] text-gray-500 mt-1 block">
                  Mandatory under CBDT rules for 80G tax benefit claim.
                </span>
              </div>

              <div>
                <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                  Phone Number (Optional)
                </label>
                <input
                  type="tel"
                  placeholder="+91 98765 43210"
                  value={donorPhone}
                  onChange={(e) => setDonorPhone(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 dark:text-gray-300 mb-1">
                Postal Address (Optional, for official tax invoice)
              </label>
              <input
                type="text"
                placeholder="House / Flat No, Street, City, State, PIN"
                value={donorAddress}
                onChange={(e) => setDonorAddress(e.target.value)}
                className="w-full px-3.5 py-2 rounded-xl border border-gray-300 dark:border-gray-700 bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-emerald-500 focus:outline-none text-sm"
              />
            </div>
          </div>

          {/* DPDP Act 2023 Consent Checkbox */}
          <div className="flex items-start gap-3 p-3.5 bg-emerald-50/60 rounded-xl border border-emerald-200/80">
            <input
              type="checkbox"
              id="donate-dpdp-consent"
              required
              checked={dpdpConsent}
              onChange={(e) => setDpdpConsent(e.target.checked)}
              className="w-4 h-4 mt-0.5 accent-emerald-600 rounded cursor-pointer"
            />
            <label htmlFor="donate-dpdp-consent" className="text-xs text-slate-700 leading-relaxed cursor-pointer">
              I consent to the collection and processing of my name, email, and PAN by Animal Guardian 360° under the <Link href="/privacy" target="_blank" className="text-emerald-700 underline font-semibold">Digital Personal Data Protection Act, 2023 (DPDP Act)</Link> solely for Section 80G tax receipt issuance and statutory reporting.
            </label>
          </div>

          {/* Submit Checkout Button */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={loading || !dpdpConsent}
              className="w-full py-4 px-6 bg-emerald-600 hover:bg-emerald-700 text-white rounded-2xl font-bold text-lg shadow-lg shadow-emerald-600/25 flex items-center justify-center gap-3 transition-all disabled:opacity-50"
            >
              {loading ? (
                <span>Generating Secure Order...</span>
              ) : (
                <>
                  <CreditCard className="w-5 h-5" />
                  <span>Proceed to Pay ₹{amount.toLocaleString('en-IN')} via Razorpay UPI / QR</span>
                </>
              )}
            </button>

            <p className="text-center text-xs text-gray-500 mt-3">
              Protected by 256-bit encryption. Razorpay UPI Intent, GPay, PhonePe, Paytm, and Netbanking supported.
            </p>
          </div>
        </form>
      )}

      {/* Payment Screen (UPI Intent / QR simulation) */}
      {paymentStep === 'qr_mock' && currentOrder && (
        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-gray-200 dark:border-gray-800 shadow-xl max-w-lg mx-auto text-center space-y-6">
          <div className="w-16 h-16 bg-emerald-50 dark:bg-emerald-950/60 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
            <QrCode className="w-8 h-8" />
          </div>

          <div>
            <span className="text-xs uppercase tracking-wider font-bold text-emerald-600 dark:text-emerald-400">
              Razorpay UPI Checkout
            </span>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
              ₹{currentOrder.amount_inr.toLocaleString('en-IN')}
            </h2>
            <p className="text-xs text-gray-500 mt-1 font-mono">
              Order ID: {currentOrder.order_id}
            </p>
          </div>

          <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-2xl border border-dashed border-gray-300 dark:border-gray-700 flex flex-col items-center">
            {/* Mock QR display */}
            <div className="w-48 h-48 bg-white p-3 rounded-xl shadow-inner flex flex-col items-center justify-center border border-gray-200">
              <QrCode className="w-36 h-36 text-gray-800" />
              <span className="text-[10px] font-mono text-gray-500 mt-1">Scan via any UPI App</span>
            </div>
            <p className="text-xs text-gray-600 dark:text-gray-300 mt-3 font-medium">
              Pay to: <span className="font-mono text-emerald-600">animalguardian360@razorpay</span>
            </p>
          </div>

          {errorMsg && (
            <p className="text-xs text-red-600">{errorMsg}</p>
          )}

          <div className="space-y-3">
            <button
              onClick={handleSimulatePaymentSuccess}
              disabled={loading}
              className="w-full py-3.5 px-6 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              {loading ? 'Verifying Transaction Signature...' : 'Simulate UPI Payment Success'}
            </button>

            <button
              onClick={() => setPaymentStep('form')}
              className="w-full py-2.5 px-4 text-xs font-semibold text-gray-500 hover:text-gray-800 dark:hover:text-gray-200"
            >
              Cancel / Back to Form
            </button>
          </div>
        </div>
      )}

      {/* Success & Receipt Download */}
      {paymentStep === 'completed' && verifiedDonation && (
        <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 border border-emerald-200 dark:border-emerald-800 shadow-xl max-w-lg mx-auto text-center space-y-6">
          <div className="w-16 h-16 bg-emerald-100 dark:bg-emerald-950 text-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-9 h-9" />
          </div>

          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              Thank You for Your Compassion!
            </h2>
            <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
              Your contribution of <strong className="text-emerald-600">₹{verifiedDonation.amount_inr.toLocaleString('en-IN')}</strong> has been received successfully.
            </p>
          </div>

          <div className="bg-emerald-50 dark:bg-emerald-950/40 p-4 rounded-2xl text-left border border-emerald-200 dark:border-emerald-900 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-500">Receipt Number:</span>
              <span className="font-mono font-semibold text-gray-900 dark:text-white">
                {verifiedDonation.receipt_number}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">Donor Name:</span>
              <span className="font-semibold text-gray-900 dark:text-white">
                {verifiedDonation.donor_name}
              </span>
            </div>
            {verifiedDonation.donor_pan && (
              <div className="flex justify-between">
                <span className="text-gray-500">PAN:</span>
                <span className="font-mono font-semibold text-gray-900 dark:text-white">
                  {verifiedDonation.donor_pan}
                </span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">80G Tax Exemption:</span>
              <span className="text-emerald-700 dark:text-emerald-300 font-bold">
                Eligible (50% Deduction)
              </span>
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <button
              onClick={handleDownloadReceipt}
              className="w-full py-3.5 px-6 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl font-bold shadow-md flex items-center justify-center gap-2 transition-all"
            >
              <Download className="w-4 h-4" />
              <span>Download Official 80G Tax Receipt (PDF)</span>
            </button>

            <Link
              href="/donate/transparency"
              className="inline-flex items-center justify-center w-full py-2.5 px-4 text-xs font-semibold text-emerald-600 hover:underline"
            >
              View Fund Allocation in Public Transparency Ledger →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
