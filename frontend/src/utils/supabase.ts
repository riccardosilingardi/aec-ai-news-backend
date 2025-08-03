/**
 * Supabase Client Configuration
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true
  }
});

// Database types for TypeScript
export interface Subscription {
  id: string;
  email: string;
  subscribed_at: string;
  gdpr_consent: boolean;
  consent_date: string;
  source: string;
  status: 'active' | 'unsubscribed' | 'bounced';
  preferences?: {
    newsletter: boolean;
    promotions: boolean;
    updates: boolean;
  };
}

export interface Newsletter {
  id: string;
  title: string;
  content: string;
  html_content: string;
  sent_at: string;
  subscriber_count: number;
  open_rate?: number;
  click_rate?: number;
}

export interface GDPRConsent {
  id: string;
  email: string;
  consent_type: string;
  consent_given: boolean;
  consent_date: string;
  consent_source: string;
}