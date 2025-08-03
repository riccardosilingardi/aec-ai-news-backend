/**
 * Landing Page Component - GDPR Compliant
 * 
 * TODO:
 * [ ] Newsletter value proposition section
 * [ ] Email signup form with GDPR consent checkbox
 * [ ] Privacy policy and data usage transparency
 * [ ] Sample newsletter preview
 * [ ] Testimonials and social proof  
 * [ ] Pricing information (FREE emphasis)
 * [ ] FAQ section with GDPR info
 * [ ] Footer with privacy policy and unsubscribe info
 * 
 * GDPR COMPLIANCE:
 * - Explicit consent checkbox for data processing
 * - Clear privacy policy link
 * - Data usage transparency
 * - Right to access, rectify, delete data
 * - One-click unsubscribe capability
 * - Cookie consent management
 */

import React, { useState } from 'react';
import { supabase } from '../../utils/supabase';

export const LandingPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [gdprConsent, setGdprConsent] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!gdprConsent) {
      setError('Please agree to our data processing terms');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Check if email already exists
      const { data: existingUser } = await supabase
        .from('subscriptions')
        .select('email')
        .eq('email', email)
        .single();

      if (existingUser) {
        setError('This email is already subscribed');
        return;
      }

      // Create subscription
      const { error: subscriptionError } = await supabase
        .from('subscriptions')
        .insert({
          email,
          subscribed_at: new Date().toISOString(),
          gdpr_consent: true,
          consent_date: new Date().toISOString(),
          source: 'landing_page',
          status: 'active'
        });

      if (subscriptionError) throw subscriptionError;

      // Log GDPR consent
      await supabase
        .from('gdpr_consents')
        .insert({
          email,
          consent_type: 'newsletter_subscription',
          consent_given: true,
          consent_date: new Date().toISOString(),
          consent_source: 'landing_page'
        });

      setSuccess(true);
      setEmail('');
      setGdprConsent(false);
    } catch (err) {
      setError('Failed to subscribe. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-900 to-indigo-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold mb-6">
              AEC Industry Intelligence
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100">
              Stay ahead with curated news from Architecture, Engineering & Construction
            </p>
            <p className="text-lg mb-12 text-blue-200 max-w-3xl mx-auto">
              Get the most relevant industry insights delivered to your inbox weekly. 
              100% free, AI-curated, and focused on what matters to AEC professionals.
            </p>
          </div>

          {/* Subscription Form */}
          <div className="max-w-md mx-auto bg-white rounded-lg shadow-xl p-6">
            <h3 className="text-2xl font-bold text-gray-900 mb-4 text-center">
              Join 10,000+ AEC Professionals
            </h3>
            
            {success ? (
              <div className="text-center">
                <div className="text-green-600 text-5xl mb-4">✓</div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  Successfully Subscribed!
                </h4>
                <p className="text-gray-600">
                  Check your email for confirmation and your first newsletter.
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubscribe} className="space-y-4">
                <div>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your professional email"
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 text-gray-900"
                  />
                </div>

                {error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <p className="text-red-800 text-sm">{error}</p>
                  </div>
                )}

                {/* GDPR Consent */}
                <div className="space-y-3">
                  <label className="flex items-start space-x-3">
                    <input
                      type="checkbox"
                      checked={gdprConsent}
                      onChange={(e) => setGdprConsent(e.target.checked)}
                      required
                      className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    />
                    <span className="text-sm text-gray-700">
                      I agree to receive the weekly AEC newsletter and understand that I can 
                      unsubscribe at any time. I consent to the processing of my email address 
                      for this purpose as described in the{' '}
                      <a href="/privacy" className="text-blue-600 hover:underline">
                        Privacy Policy
                      </a>.
                    </span>
                  </label>
                </div>

                <button
                  type="submit"
                  disabled={loading || !gdprConsent}
                  className="w-full bg-blue-600 text-white py-3 px-6 rounded-md font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                >
                  {loading ? 'Subscribing...' : 'Get Free Newsletter'}
                </button>

                <p className="text-xs text-gray-500 text-center">
                  100% free • No spam • Unsubscribe anytime • GDPR compliant
                </p>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* Value Proposition */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Why 10,000+ AEC Professionals Trust Us
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Our AI-powered system scans hundreds of sources to deliver only the most relevant, 
              high-quality content for your industry.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-blue-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🎯</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Curated Content</h3>
              <p className="text-gray-600">
                AI-powered curation ensures you only get the most relevant and valuable content for AEC professionals.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-green-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">⚡</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Time Saving</h3>
              <p className="text-gray-600">
                Spend 5 minutes reading instead of hours searching. Get your weekly dose of industry intelligence.
              </p>
            </div>

            <div className="text-center">
              <div className="bg-purple-100 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🔒</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Privacy First</h3>
              <p className="text-gray-600">
                GDPR compliant with full transparency. Your data is secure and you can unsubscribe anytime.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Sample Newsletter Preview */}
      <section className="py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              What You'll Receive
            </h2>
            <p className="text-xl text-gray-600">
              A sample of our weekly newsletter content
            </p>
          </div>

          <div className="bg-white border border-gray-200 rounded-lg shadow-lg overflow-hidden">
            <div className="bg-blue-600 text-white p-4">
              <h3 className="text-xl font-bold">AEC Weekly Intelligence</h3>
              <p className="text-blue-100">Week of January 15, 2024</p>
            </div>
            
            <div className="p-6 space-y-6">
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  🏗️ This Week's Top Stories
                </h4>
                <ul className="space-y-2 text-gray-600">
                  <li>• Revolutionary BIM technology increases project efficiency by 40%</li>
                  <li>• New sustainable building materials approved for commercial use</li>
                  <li>• AI-powered construction management reduces delays by 25%</li>
                </ul>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  📈 Market Insights
                </h4>
                <p className="text-gray-600">
                  Construction spending increased 3.2% this quarter, driven by commercial projects and infrastructure investments...
                </p>
              </div>

              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">
                  🔧 Tech Spotlight
                </h4>
                <p className="text-gray-600">
                  Drone technology for site surveys is becoming mainstream, with 60% of major firms adopting UAV solutions...
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-gray-900 mb-12">
            Frequently Asked Questions
          </h2>

          <div className="space-y-8">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                How do you ensure content quality?
              </h3>
              <p className="text-gray-600">
                Our AI system analyzes hundreds of sources and uses quality scoring algorithms to select only the most relevant, accurate, and valuable content for AEC professionals.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Is my data safe and GDPR compliant?
              </h3>
              <p className="text-gray-600">
                Yes, we are fully GDPR compliant. We only collect your email address with explicit consent, and you can access, modify, or delete your data at any time. We never share your information with third parties.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Can I unsubscribe easily?
              </h3>
              <p className="text-gray-600">
                Absolutely. Every email includes a one-click unsubscribe link, and you can also manage your preferences or request complete data deletion at any time.
              </p>
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                Is this really free?
              </h3>
              <p className="text-gray-600">
                Yes, our weekly newsletter is completely free with no hidden costs. We may introduce premium features in the future, but the core newsletter will always remain free.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="text-2xl font-bold mb-4">AEC AI News</h3>
            <p className="text-gray-400 mb-6">
              Intelligent news curation for the Architecture, Engineering & Construction industry
            </p>
            
            <div className="flex justify-center space-x-6 text-sm">
              <a href="/privacy" className="text-gray-400 hover:text-white">Privacy Policy</a>
              <a href="/terms" className="text-gray-400 hover:text-white">Terms of Service</a>
              <a href="/unsubscribe" className="text-gray-400 hover:text-white">Unsubscribe</a>
              <a href="/contact" className="text-gray-400 hover:text-white">Contact</a>
            </div>
            
            <p className="text-gray-500 text-xs mt-6">
              © 2024 AEC AI News. GDPR Compliant. Made with ❤️ for the AEC community.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};