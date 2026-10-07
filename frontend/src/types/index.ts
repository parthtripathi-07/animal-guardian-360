export interface User {
  id: string;
  phone?: string;
  email?: string;
  full_name?: string;
  avatar_url?: string;
  role: 'user' | 'hospital' | 'admin';
  is_active: boolean;
  is_verified: boolean;
  strike_count: number;
  is_reporting_suspended: boolean;
  preferred_locale: 'en' | 'hi';
}

export interface VetHospital {
  id: string;
  place_id?: string;
  name: string;
  phone: string;
  emergency_phone?: string;
  email?: string;
  address: string;
  latitude: number;
  longitude: number;
  is_24x7: boolean;
  is_verified: boolean;
  is_active: boolean;
  ambulance_available: boolean;
  rating: number;
  total_ratings: number;
  distance_meters?: number;
  open_now?: boolean;
}

export interface NearbyVetsResponse {
  success: boolean;
  latitude: number;
  longitude: number;
  radius_km: number;
  count: number;
  cached: boolean;
  source: string;
  vets: VetHospital[];
}

export interface AlertDispatch {
  id: string;
  hospital_id: string;
  hospital_name: string;
  hospital_phone: string;
  escalation_round: number;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  expires_at: string;
  dispatched_at: string;
}

export interface AccidentAlert {
  id: string;
  reporter_id?: string;
  reporter_phone?: string;
  animal_type: string;
  condition_description?: string;
  photo_url?: string;
  latitude: number;
  longitude: number;
  address_text?: string;
  status: 'alerted' | 'accepted' | 'reached' | 'closed' | 'cancelled';
  accepted_hospital_id?: string;
  accepted_hospital_name?: string;
  accepted_hospital_phone?: string;
  eta_minutes?: number;
  created_at: string;
  dispatches: AlertDispatch[];
}

export interface LostFoundPostResponse {
  id: string;
  user_id?: string;
  pet_id?: string;
  post_type: 'lost' | 'found' | 'sighting';
  species: string;
  breed?: string;
  primary_color?: string;
  secondary_color?: string;
  gender?: string;
  distinctive_marks?: string;
  collar_info?: string;
  incident_date: string;
  latitude: number;
  longitude: number;
  address_text?: string;
  photo_urls: string[];
  status: 'active' | 'reunited' | 'closed';
  masked_contact_enabled: boolean;
  distance_meters?: number;
  created_at: string;
}

