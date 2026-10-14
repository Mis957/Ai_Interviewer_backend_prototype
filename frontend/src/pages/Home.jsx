import HomeHero from '../components/home/HomeHero'
import StatementSection from '../components/home/StatementSection'
import ProblemSection from '../components/home/ProblemSection'
import FeaturesSection from '../components/home/FeaturesSection'
import PracticeLoop from '../components/home/PracticeLoop'
import HowItWorksSection from '../components/home/HowItWorksSection'
import InterviewPrepSection from '../components/home/InterviewPrepSection'
import PricingSection from '../components/home/PricingSection'
import FaqSection from '../components/home/FaqSection'
import FinalCtaSection from '../components/home/FinalCtaSection'
import Footer from '../components/home/Footer'

export default function Home() {
  return (
    <main className="home-main">
      <HomeHero />
      <StatementSection />
      <ProblemSection />
      <FeaturesSection />
      <PracticeLoop />
      <HowItWorksSection />
      <InterviewPrepSection />
      <PricingSection />
      <FaqSection />
      <FinalCtaSection />
      <Footer />
    </main>
  )
}
