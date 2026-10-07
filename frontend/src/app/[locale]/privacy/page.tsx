'use client';

import React from 'react';
import Link from 'next/link';
import { 
  ShieldCheck, 
  Lock, 
  Eye, 
  FileText, 
  CheckCircle, 
  Mail, 
  UserCheck, 
  AlertCircle, 
  HelpCircle,
  ArrowLeft
} from 'lucide-react';

export default function PrivacyPolicyPage({ params: { locale } }: { params: { locale: string } }) {
  const isHindi = locale === 'hi';

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 space-y-10">
      {/* Top Header */}
      <div className="space-y-3 border-b border-slate-200 dark:border-slate-800 pb-8">
        <Link
          href={`/${locale}`}
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 hover:text-emerald-700 mb-2"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>{isHindi ? 'मुखपृष्ठ पर वापस जाएं' : 'Back to Home'}</span>
        </Link>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
            <ShieldCheck className="w-4 h-4" />
            <span>DPDP Act, 2023 Compliant</span>
          </span>
          <span className="text-xs text-slate-500 font-mono">
            {isHindi ? 'अंतिम संशोधन: अक्टूबर 2026' : 'Last Updated: October 2026'}
          </span>
        </div>

        <h1 className="text-3xl sm:text-4xl font-black text-slate-900 dark:text-white">
          {isHindi ? 'गोपनीयता नीति एवं डेटा सुरक्षा' : 'Privacy Policy & Data Protection'}
        </h1>
        <p className="text-sm text-slate-600 dark:text-slate-400 max-w-3xl leading-relaxed">
          {isHindi
            ? 'एनिमल गार्जियन 360° भारत के डिजिटल व्यक्तिगत डेटा संरक्षण अधिनियम (DPDP Act, 2023) के प्रावधानों के तहत नागरिकों के डेटा की सुरक्षा, गोपनीयता और स्वायत्तता के लिए पूरी तरह प्रतिबद्ध है।'
            : 'Animal Guardian 360° is strictly committed to protecting citizen personal data, privacy, and autonomy in full compliance with the Digital Personal Data Protection Act (DPDP Act, 2023) of India.'}
        </p>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <div className="w-9 h-9 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">
            {isHindi ? 'गोपनीयता आधारित डिज़ाइन' : 'Privacy by Design'}
          </h3>
          <p className="text-xs text-slate-500">
            {isHindi
              ? 'अपलोड किए गए फोटो से कैमरा जीपीएस (EXIF) को सार्वजनिक प्रदर्शन से स्वतः हटा दिया जाता है।'
              : 'Uploaded incident photos automatically strip embedded camera GPS (EXIF) from public exposure.'}
          </p>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <div className="w-9 h-9 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center">
            <Eye className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">
            {isHindi ? 'मास्क्ड संपर्क रिले' : 'Masked Contact Relay'}
          </h3>
          <p className="text-xs text-slate-500">
            {isHindi
              ? 'खोए पालतू जानवरों के स्वामियों के फोन नंबर सार्वजनिक नहीं किए जाते; सभी बातचीत इन-ऐप सुरक्षित रिले द्वारा होती है।'
              : 'Pet owner phone numbers are never displayed publicly; contact is mediated via secure masked relays.'}
          </p>
        </div>

        <div className="p-5 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-2">
          <div className="w-9 h-9 bg-purple-50 text-purple-600 rounded-xl flex items-center justify-center">
            <UserCheck className="w-5 h-5" />
          </div>
          <h3 className="font-bold text-sm text-slate-900 dark:text-white">
            {isHindi ? 'डेटा प्रिंसिपल के अधिकार' : 'Data Principal Rights'}
          </h3>
          <p className="text-xs text-slate-500">
            {isHindi
              ? 'आपको अपने डेटा की समीक्षा करने, सुधार करने और 7 दिनों के भीतर हटाने का पूर्ण कानूनी अधिकार है।'
              : 'You possess full statutory rights to access, correct, and request erasure of your data within 7 days.'}
          </p>
        </div>
      </div>

      {/* Policy Clauses Accordion/Sections */}
      <div className="space-y-8 text-sm text-slate-700 dark:text-slate-300 leading-relaxed bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm">
        {/* 1. Data Fiduciary */}
        <section className="space-y-3">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">1</span>
            <span>{isHindi ? 'डेटा फिड्यूशरी की पहचान (Data Fiduciary)' : 'Data Fiduciary Identification'}</span>
          </h2>
          <p>
            {isHindi
              ? 'एनिमल गार्जियन 360° फाउंडेशन (Animal Guardian 360° Foundation) भारतीय कानून के अंतर्गत पंजीकृत एक गैर-लाभकारी संगठन है, जो इस प्लेटफ़ॉर्म पर संसाधित किए जाने वाले सभी व्यक्तिगत डेटा का डेटा फिड्यूशरी (Data Fiduciary) है।'
              : 'Animal Guardian 360° Foundation is the registered Data Fiduciary responsible for determining the purpose and means of processing personal data across this application under the DPDP Act, 2023.'}
          </p>
        </section>

        {/* 2. Categories of Personal Data Collected */}
        <section className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-6">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">2</span>
            <span>{isHindi ? 'एकत्रित किए जाने वाले डेटा की श्रेणियां' : 'Categories of Personal Data Collected'}</span>
          </h2>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-600 dark:text-slate-400">
            <li>
              <strong>{isHindi ? 'पहचान एवं संपर्क डेटा:' : 'Identity & Contact:'}</strong> {isHindi ? 'फोन नंबर (OTP लॉगिन), नाम, और ईमेल पता।' : 'Phone number (E.164 verified via OTP), full name, and email address.'}
            </li>
            <li>
              <strong>{isHindi ? 'स्थान डेटा (Geolocation):' : 'Location Data:'}</strong> {isHindi ? 'आपातकालीन सड़क दुर्घटना SOS एवं क्रूरता रिपोर्ट के समय डिवाइस द्वारा प्रदत्त सटीक GPS निर्देशांक।' : 'Precise device GPS coordinates captured with user consent during road accident SOS and cruelty reports.'}
            </li>
            <li>
              <strong>{isHindi ? 'साक्ष्य एवं मीडिया:' : 'Evidence Media:'}</strong> {isHindi ? 'घटना से संबंधित फोटो एवं वीडियो (जिनसे सार्वजनिक प्रदर्शन से पहले कैमरा EXIF मेटाडेटा हटा दिया जाता है)।' : 'Incident photographs and videos (sanitized of camera EXIF metadata prior to public storage).'}
            </li>
            <li>
              <strong>{isHindi ? 'कर छूट डेटा (धारा 80G):' : 'Statutory Tax Data (Section 80G):'}</strong> {isHindi ? 'दानदाताओं का भारतीय PAN नंबर और डाक पता (आयकर विभाग की वैधानिक आवश्यकताओं के अनुसार)।' : 'Indian Permanent Account Number (PAN) and postal address required for CBDT Section 80G tax deductions.'}
            </li>
          </ul>
        </section>

        {/* 3. Specified Purposes */}
        <section className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-6">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">3</span>
            <span>{isHindi ? 'डेटा प्रसंस्करण के निर्दिष्ट वैधानिक उद्देश्य' : 'Specified Purposes for Data Processing'}</span>
          </h2>
          <p>
            {isHindi
              ? 'डेटा केवल निम्नलिखित विशिष्ट उद्देश्यों के लिए एकत्र और संसाधित किया जाता है:'
              : 'Personal data is strictly processed solely for the following specified, legitimate purposes:'}
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="font-bold text-slate-900 dark:text-white block mb-1">
                {isHindi ? '1. आपातकालीन SOS प्रेषण' : '1. Emergency SOS Dispatch'}
              </span>
              <span>{isHindi ? 'घायल जानवर की सहायता के लिए 3 नजदीकी अस्पतालों को स्थान भेजना।' : 'Relaying live GPS coordinates to the 3 nearest animal hospitals.'}</span>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="font-bold text-slate-900 dark:text-white block mb-1">
                {isHindi ? '2. पुलिस शिकायत दस्तावेज़ीकरण' : '2. Police Complaint Preparation'}
              </span>
              <span>{isHindi ? 'नागरिकों के लिए फॉर्म AC-1 पुलिस शिकायत PDF तैयार करना।' : 'Generating police-compliant Form AC-1 summaries under PCA Act 1960.'}</span>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="font-bold text-slate-900 dark:text-white block mb-1">
                {isHindi ? '3. पालतू जानवर AI मिलान' : '3. AI Lost Pet Recovery'}
              </span>
              <span>{isHindi ? 'खोए और पाए गए पालतू जानवरों के बीच 25 किमी के दायरे में वेक्टर तुलना।' : 'Running 512-dim visual vector similarity matching within 25 km.'}</span>
            </div>
            <div className="p-3 bg-slate-50 dark:bg-slate-800/50 rounded-xl border border-slate-200 dark:border-slate-800">
              <span className="font-bold text-slate-900 dark:text-white block mb-1">
                {isHindi ? '4. 80G कर रसीद जारी करना' : '4. Statutory 80G Receipting'}
              </span>
              <span>{isHindi ? 'आयकर विभाग को दानदाता रिपोर्टिंग एवं ऑडिट बहीखाता।' : 'Complying with CBDT electronic filing and statutory audit trails.'}</span>
            </div>
          </div>
        </section>

        {/* 4. Data Principal Rights */}
        <section className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-6">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">4</span>
            <span>{isHindi ? 'डेटा प्रिंसिपल के कानूनी अधिकार (आपके अधिकार)' : 'Your Rights as a Data Principal'}</span>
          </h2>
          <div className="space-y-2 text-xs">
            <p>
              <strong>{isHindi ? 'पहुंच का अधिकार (Right to Access):' : 'Right to Access:'}</strong> {isHindi ? 'आप अपने व्यक्तिगत डेटा का सारांश और प्रसंस्करण की जानकारी कभी भी प्राप्त कर सकते हैं।' : 'Request a digital export of all personal data held about you.'}
            </p>
            <p>
              <strong>{isHindi ? 'सुधार एवं विलोपन का अधिकार (Right to Correction & Erasure):' : 'Right to Correction & Erasure:'}</strong> {isHindi ? 'आप अपूर्ण या गलत डेटा को सही करवा सकते हैं और अपना खाता तथा संबंधित गैर-वैधानिक डेटा मिटाने का अनुरोध कर सकते हैं।' : 'Correct inaccurate data or request deletion of account and incident history not mandated by statutory law.'}
            </p>
            <p>
              <strong>{isHindi ? 'सहमति वापस लेने का अधिकार (Right to Withdraw Consent):' : 'Right to Withdraw Consent:'}</strong> {isHindi ? 'आप किसी भी समय अपनी सहमति वापस ले सकते हैं।' : 'Withdraw consent at any time via in-app profile settings.'}
            </p>
            <p>
              <strong>{isHindi ? 'नामांकन का अधिकार (Right to Nominate):' : 'Right to Nominate:'}</strong> {isHindi ? 'मृत्यु या अक्षमता की स्थिति में अपने डेटा अधिकारों के प्रयोग हेतु किसी अन्य व्यक्ति को नामांकित कर सकते हैं।' : 'Designate a nominee to exercise data rights in the event of death or incapacity.'}
            </p>
          </div>
        </section>

        {/* 5. Grievance Redressal Officer */}
        <section className="space-y-3 border-t border-slate-100 dark:border-slate-800 pt-6">
          <h2 className="text-lg font-extrabold text-slate-900 dark:text-white flex items-center gap-2">
            <span className="w-6 h-6 rounded-full bg-emerald-600 text-white text-xs flex items-center justify-center font-bold">5</span>
            <span>{isHindi ? 'डेटा संरक्षण एवं शिकायत निवारण अधिकारी (DPO Contact)' : 'Data Protection Officer & Grievance Redressal'}</span>
          </h2>
          <p className="text-xs">
            {isHindi
              ? 'DPDP Act, 2023 की धारा 13 के तहत किसी भी शिकायत या डेटा अधिकार के प्रयोग हेतु हमारे नियुक्त अधिकारी से संपर्क करें:'
              : 'Pursuant to Section 13 of the DPDP Act, 2023, contact our designated Grievance & Data Protection Officer:'}
          </p>

          <div className="p-4 bg-slate-50 dark:bg-slate-800/60 rounded-2xl border border-slate-200 dark:border-slate-700 space-y-1.5 text-xs">
            <div className="font-bold text-slate-900 dark:text-white">
              {isHindi ? 'डेटा संरक्षण अधिकारी (DPO):' : 'Data Protection Officer (DPO):'} Adv. Shreya Deshmukh
            </div>
            <div>
              <strong>{isHindi ? 'ईमेल:' : 'Email:'}</strong> <a href="mailto:dpo@animalguardian360.org" className="text-emerald-600 underline">dpo@animalguardian360.org</a>
            </div>
            <div>
              <strong>{isHindi ? 'शिकायत निवारण समय सीमा (SLA):' : 'Resolution SLA:'}</strong> {isHindi ? '7 कार्य दिवस' : '7 business days'}
            </div>
            <div>
              <strong>{isHindi ? 'अपील प्राधिकरण:' : 'Appellate Authority:'}</strong> {isHindi ? 'डेटा संरक्षण बोर्ड (Data Protection Board of India)' : 'Data Protection Board of India'}
            </div>
          </div>
        </section>
      </div>

      {/* Consent Callout */}
      <div className="p-6 bg-emerald-50 dark:bg-emerald-950/40 rounded-3xl border border-emerald-200 dark:border-emerald-800 flex items-start gap-4">
        <CheckCircle className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-0.5" />
        <div className="space-y-1 text-xs">
          <h4 className="font-bold text-emerald-900 dark:text-emerald-200 text-sm">
            {isHindi ? 'पारदर्शिता एवं विश्वास' : 'Transparency & Ground Reality'}
          </h4>
          <p className="text-emerald-800 dark:text-emerald-300 leading-relaxed">
            {isHindi
              ? 'एनिमल गार्जियन 360° कभी भी आपका व्यक्तिगत डेटा किसी तीसरे पक्ष के विज्ञापनदाताओं या डेटा ब्रोकरों को नहीं बेचता। हमारा एकमात्र उद्देश्य बेजुबान जानवरों की त्वरित रक्षा करना है।'
              : 'Animal Guardian 360° never sells or monetizes personal data with third-party advertisers or data brokers. All data exists purely to accelerate ground rescue operations.'}
          </p>
        </div>
      </div>
    </div>
  );
}

