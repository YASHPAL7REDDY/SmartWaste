import { Link } from 'react-router-dom'
import { GlassCard, GlassButton, Navbar } from '../components'

export function About() {
  return (
    <div className="page-container pt-20">
      <Navbar />
      <div className="section-container max-w-4xl">
        <div className="mb-12 text-center">
          <h1 className="text-4xl font-bold text-text-primary mb-4">About SmartWaste</h1>
          <p className="text-xl text-text-secondary">AI-Powered Waste Management for Smart Cities</p>
        </div>
        
        <div className="space-y-8">
          <GlassCard>
            <h2 className="text-2xl font-bold text-text-primary mb-4">Our Mission</h2>
            <p className="text-text-secondary leading-relaxed mb-4">
              SmartWaste is an intelligent waste management platform that leverages machine learning to predict, 
              prevent, and optimize waste collection. Our goal is to create cleaner, more sustainable cities 
              through data-driven decision making.
            </p>
            <p className="text-text-secondary leading-relaxed">
              By combining real-time waste submissions with trained ML models, we provide accurate next-day 
              and day-after-tomorrow predictions for six waste categories: wet, dry, plastic, glass, metal, and medical.
            </p>
          </GlassCard>
          
          <GlassCard>
            <h2 className="text-2xl font-bold text-text-primary mb-4">How It Works</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[
                { step: '1', title: 'Submit', desc: 'Users submit separated waste data daily', icon: '📝' },
                { step: '2', title: 'Predict', desc: 'ML models forecast tomorrow\'s waste by type', icon: '🔮' },
                { step: '3', title: 'Plan', desc: 'Collectors get optimized routes & capacity', icon: '🗺️' },
                { step: '4', title: 'Collect', desc: 'Waste collected by type, sent to proper facilities', icon: '♻️' },
              ].map((item) => (
                <div key={item.step} className="text-center">
                  <div className="w-16 h-16 rounded-full bg-emerald/10 border border-emerald/30 flex items-center justify-center mx-auto mb-4 text-3xl">
                    {item.icon}
                  </div>
                  <div className="text-2xl font-bold text-emerald mb-1">{item.step}</div>
                  <h3 className="font-semibold text-text-primary mb-1">{item.title}</h3>
                  <p className="text-sm text-text-secondary">{item.desc}</p>
                </div>
              ))}
            </div>
          </GlassCard>
          
          <GlassCard>
            <h2 className="text-2xl font-bold text-text-primary mb-4">Key Features</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[
                { title: 'Six Waste Categories', desc: 'Wet, Dry, Plastic, Glass, Metal, Medical - all tracked separately' },
                { title: 'ML Predictions', desc: 'Random Forest & XGBoost models for next-day & day-after forecasting' },
                { title: 'Overflow Risk', desc: 'Area-level risk scoring with capacity utilization analysis' },
                { title: 'Smart Routing', desc: 'OR-Tools optimization considering priority, risk & vehicle capacity' },
                { title: 'Facility Matching', desc: 'Medical waste → biomedical only; each type to correct facility' },
                { title: 'Accuracy Tracking', desc: 'MAE, RMSE, MAPE metrics comparing predicted vs actual collection' },
              ].map((feature, i) => (
                <div key={i} className="p-4 bg-glass-white/50 rounded-glass-sm">
                  <h3 className="font-semibold text-text-primary mb-1">{feature.title}</h3>
                  <p className="text-sm text-text-secondary">{feature.desc}</p>
                </div>
              ))}
            </div>
          </GlassCard>
          
          <GlassCard>
            <h2 className="text-2xl font-bold text-text-primary mb-4">Data & Privacy</h2>
            <p className="text-text-secondary leading-relaxed mb-4">
              SmartWaste uses your submission history to train and improve prediction models. Your personal data 
              is encrypted and never shared with third parties. Area-level predictions are aggregated and anonymized.
            </p>
            <p className="text-text-secondary leading-relaxed">
              The system is built on verified ML models trained on synthetic and real waste data, 
              with 4 trained models covering total waste and per-type predictions.
            </p>
          </GlassCard>
        </div>
        
        <div className="text-center mt-12">
          <Link to="/collect">
            <GlassButton variant="primary" className="w-full sm:w-auto">
              Start Using SmartWaste
            </GlassButton>
          </Link>
        </div>
      </div>
    </div>
  )
}