import { NavBar } from './NavBar';
import { HeroSection } from './HeroSection';
import { FeaturesSection } from './FeaturesSection';
import { ProcessTimeline } from './ProcessTimeline';
import { BenefitsSection } from './BenefitsSection';
import { CTASection } from './CTASection';
import { Footer } from './Footer';
import styles from './LandingPage.module.css';

interface LandingPageProps {
  onNavigateToLogin: () => void;
}

export function LandingPage({ onNavigateToLogin }: LandingPageProps) {
  const handleLoginClick = () => {
    onNavigateToLogin();
  };

  const handleLearnMoreClick = () => {
    const featuresSection = document.querySelector('[data-section="features"]');
    featuresSection?.scrollIntoView({ behavior: 'smooth' });
  };

  return (
    <div className={styles.landingPage}>
      <NavBar />
      
      <main className={styles.main}>
        <HeroSection 
          onLoginClick={handleLoginClick}
          onLearnMoreClick={handleLearnMoreClick}
        />
        
        <div data-section="features">
          <FeaturesSection />
        </div>
        
        <div data-section="process">
          <ProcessTimeline />
        </div>
        
        <div data-section="benefits">
          <BenefitsSection />
        </div>
        
        <CTASection onLoginClick={handleLoginClick} />
      </main>
      
      <Footer />
    </div>
  );
}
