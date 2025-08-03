/**
 * GDPR Compliant Unsubscribe Component
 * 
 * TODO:
 * [ ] One-click unsubscribe from email links
 * [ ] Preference center for partial unsubscribe  
 * [ ] Data deletion request handling
 * [ ] GDPR compliance confirmation
 * [ ] Feedback collection (optional)
 * [ ] Re-subscribe option with new consent
 */

import React, { useState, useEffect } from 'react';
import { supabase } from '../../utils/supabase';

interface UnsubscribeProps {
  token?: string;
  userId?: string;
}

interface SubscriptionPreferences {
  newsletter: boolean;
  promotions: boolean;
  updates: boolean;
  all: boolean;
}

export const UnsubscribeHandler: React.FC<UnsubscribeProps> = ({ token, userId }) => {
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPreferences, setShowPreferences] = useState(false);
  const [preferences, setPreferences] = useState<SubscriptionPreferences>({
    newsletter: true,
    promotions: true,
    updates: true,
    all: false
  });
  const [feedback, setFeedback] = useState('');

  useEffect(() => {
    if (token) {
      verifyUnsubscribeToken(token);
    }
  }, [token]);

  const verifyUnsubscribeToken = async (token: string) => {
    try {
      setLoading(true);
      // Verify the unsubscribe token
      const { data, error } = await supabase
        .from('unsubscribe_tokens')
        .select('*')
        .eq('token', token)
        .single();

      if (error || !data) {
        setError('Invalid or expired unsubscribe link');
        return;
      }

      // Load current preferences
      loadUserPreferences(data.user_id);
    } catch (err) {
      setError('Failed to verify unsubscribe token');
    } finally {
      setLoading(false);
    }
  };

  const loadUserPreferences = async (userId: string) => {
    try {
      const { data, error } = await supabase
        .from('user_preferences')
        .select('*')
        .eq('user_id', userId)
        .single();

      if (data) {
        setPreferences({
          newsletter: data.newsletter_enabled,
          promotions: data.promotions_enabled,
          updates: data.updates_enabled,
          all: false
        });
      }
    } catch (err) {
      console.error('Failed to load preferences:', err);
    }
  };

  const handleUnsubscribeAll = async () => {
    try {
      setLoading(true);
      
      // Update subscription preferences
      const { error } = await supabase
        .from('user_preferences')
        .update({
          newsletter_enabled: false,
          promotions_enabled: false,
          updates_enabled: false,
          unsubscribed_at: new Date().toISOString(),
          unsubscribe_reason: feedback || 'User requested unsubscribe'
        })
        .eq('user_id', userId);

      if (error) throw error;

      // Log GDPR compliance action
      await supabase
        .from('gdpr_actions')
        .insert({
          user_id: userId,
          action_type: 'unsubscribe_all',
          action_date: new Date().toISOString(),
          details: { feedback }
        });

      setSuccess(true);
    } catch (err) {
      setError('Failed to unsubscribe. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdatePreferences = async () => {
    try {
      setLoading(true);

      const { error } = await supabase
        .from('user_preferences')
        .update({
          newsletter_enabled: preferences.newsletter,
          promotions_enabled: preferences.promotions,
          updates_enabled: preferences.updates,
          updated_at: new Date().toISOString()
        })
        .eq('user_id', userId);

      if (error) throw error;

      setSuccess(true);
    } catch (err) {
      setError('Failed to update preferences. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDataDeletion = async () => {
    if (!confirm('Are you sure you want to delete all your data? This action cannot be undone.')) {
      return;
    }

    try {
      setLoading(true);

      // Request data deletion (GDPR Right to be Forgotten)
      const { error } = await supabase
        .from('data_deletion_requests')
        .insert({
          user_id: userId,
          requested_at: new Date().toISOString(),
          reason: feedback || 'User requested data deletion',
          status: 'pending'
        });

      if (error) throw error;

      // Log GDPR compliance action
      await supabase
        .from('gdpr_actions')
        .insert({
          user_id: userId,
          action_type: 'data_deletion_request',
          action_date: new Date().toISOString(),
          details: { feedback }
        });

      setSuccess(true);
    } catch (err) {
      setError('Failed to submit data deletion request. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Processing your request...</p>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <div className="text-green-600 text-6xl mb-4">✓</div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Processed</h2>
          <p className="text-gray-600 mb-4">
            Your preferences have been updated successfully. You can close this window.
          </p>
          <p className="text-sm text-gray-500">
            If you change your mind, you can always re-subscribe with new consent.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full mx-auto">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
            Manage Your Subscription
          </h2>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4 mb-6">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {!showPreferences ? (
            <div className="space-y-4">
              <p className="text-gray-600">
                We're sorry to see you want to unsubscribe. You can either:
              </p>

              <button
                onClick={() => setShowPreferences(true)}
                className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
              >
                Manage Email Preferences
              </button>

              <button
                onClick={handleUnsubscribeAll}
                disabled={loading}
                className="w-full bg-gray-600 text-white py-2 px-4 rounded-md hover:bg-gray-700 transition-colors"
              >
                Unsubscribe from All Emails
              </button>

              <button
                onClick={handleDataDeletion}
                className="w-full bg-red-600 text-white py-2 px-4 rounded-md hover:bg-red-700 transition-colors"
              >
                Delete All My Data (GDPR)
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Email Preferences</h3>
              
              <div className="space-y-3">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences.newsletter}
                    onChange={(e) => setPreferences(prev => ({ ...prev, newsletter: e.target.checked }))}
                    className="mr-3"
                  />
                  <span>AEC Industry Newsletter (Weekly)</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences.updates}
                    onChange={(e) => setPreferences(prev => ({ ...prev, updates: e.target.checked }))}
                    className="mr-3"
                  />
                  <span>Product Updates & Improvements</span>
                </label>

                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={preferences.promotions}
                    onChange={(e) => setPreferences(prev => ({ ...prev, promotions: e.target.checked }))}
                    className="mr-3"
                  />
                  <span>Special Offers & Promotions</span>
                </label>
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Feedback (Optional)
                </label>
                <textarea
                  value={feedback}
                  onChange={(e) => setFeedback(e.target.value)}
                  placeholder="Help us improve by telling us why you're unsubscribing..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  rows={3}
                />
              </div>

              <div className="flex space-x-3 mt-6">
                <button
                  onClick={handleUpdatePreferences}
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
                >
                  Update Preferences
                </button>
                <button
                  onClick={() => setShowPreferences(false)}
                  className="flex-1 bg-gray-300 text-gray-700 py-2 px-4 rounded-md hover:bg-gray-400 transition-colors"
                >
                  Back
                </button>
              </div>
            </div>
          )}

          <div className="mt-6 text-xs text-gray-500 text-center">
            <p>
              This action is GDPR compliant. Your data will be processed according to our{' '}
              <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};