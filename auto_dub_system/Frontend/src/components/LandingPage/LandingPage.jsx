import React from 'react';

import HeroSection from './sections/HeroSection';
import FeaturesSection from './sections/FeaturesSection';
import AIDubbingSection from './sections/AIDubbingSection';
import SolutionsGrid from './sections/SolutionsGrid';
import WhyDubbify from './sections/WhyDubbify';
import Footer from './sections/Footer';

const LandingPage = () => {
  return (
    <div
      className="min-h-screen font-sans text-gray-900 selection:bg-purple-200 overflow-x-hidden bg-white"
    >

      <HeroSection />
      <FeaturesSection />
      <AIDubbingSection />
      <SolutionsGrid />
      <WhyDubbify />
      <Footer />
    </div>
  );
};

export default LandingPage;
