import React from 'react';
import { useNavigate } from 'react-router-dom';
import megaphone from '../../../assets/megaphone.png';
import abstractWaves from '../../../assets/abstract_waves.png';
import microphone from '../../../assets/microphone.png';
import purpleRibbed from '../../../assets/purple_ribbed.png';

const HeroSection = () => {
    const navigate = useNavigate();
    return (
        <section
            className="w-full"
            style={{
                background: 'linear-gradient(180deg, #E9E5FF 0%, rgba(247, 247, 250, 0) 100%)',
            }}
        >
            <div className="pt-12 pb-20 px-6 max-w-7xl mx-auto">
                {/* Text Content */}
                <div className="text-center max-w-5xl mx-auto mb-16 animate-fade-in-up">
                    <h1 className="text-6xl md:text-7xl font-bold mb-8 tracking-tight leading-none text-black">
                        Voice Your Vision Worldwide
                    </h1>
                    <p className="text-gray-500 text-sm md:text-base leading-relaxed max-w-3xl mx-auto font-medium">
                        We provide professional video dubbing in multiple languages, ensuring your content engages a global audience without losing the original's essence. Our team of expert linguists delivers high-quality, impactful dubbing that resonates across cultures.
                    </p>
                </div>

                {/* Visual Grid - 12 Columns */}
                <div className="grid grid-cols-1 md:grid-cols-12 gap-6 h-auto md:h-[600px] animate-fade-in-up delay-200">

                    {/* 1. Left Card: Megaphone */}
                    <div className="md:col-span-4 md:row-span-2 bg-[#BAA1FF] rounded-[40px] relative overflow-hidden flex items-center justify-center p-8 group h-[400px] md:h-full transition-transform hover:-translate-y-1 duration-500">
                        <div className="absolute inset-0 bg-gradient-to-t from-[#A68AEF] to-[#CBB5FE]"></div>
                        <img
                            src={megaphone}
                            alt="Megaphone"
                            className="relative z-10 w-[90%] drop-shadow-xl transform transition-transform duration-500 group-hover:scale-105"
                        />
                    </div>

                    {/* 2. Top Middle: Blue Waves */}
                    <div className="md:col-span-5 bg-[#AEC2FF] rounded-[40px] relative overflow-hidden flex items-center justify-center min-h-[280px] group hover:-translate-y-1 transition-transform duration-500">
                        <div className="absolute inset-0 bg-gradient-to-br from-[#CBD8FF] to-[#99B0FA]"></div>
                        <img
                            src={abstractWaves}
                            alt="Abstract Waves"
                            className="relative z-10 w-full h-full object-cover mix-blend-overlay opacity-60"
                        />
                        <div className="absolute bottom-6 right-10 w-6 h-6 rounded-full bg-white/80 shadow-lg z-20 backdrop-blur-sm animate-pulse"></div>
                    </div>

                    {/* 3. Top Right: Global Reach Badge */}
                    <div className="md:col-span-3 bg-white rounded-[40px] flex flex-col items-center justify-center p-6 text-center relative min-h-[280px] group hover:-translate-y-1 transition-transform duration-500 shadow-sm border border-purple-50">
                        <div className="w-20 h-20 bg-purple-100 rounded-full flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10 text-purple-600">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M12 21a9.004 9.004 0 008.716-6.747M12 21a9.004 9.004 0 01-8.716-6.747M12 21c2.485 0 4.5-4.03 4.5-9S14.485 3 12 3m0 18c-2.485 0-4.5-4.03-4.5-9S9.515 3 12 3m0 0a8.997 8.997 0 017.843 4.582M12 3a8.997 8.997 0 00-7.843 4.582m15.686 0A11.953 11.953 0 0112 10.5c-2.998 0-5.74-1.1-7.843-2.918m15.686 0A8.959 8.959 0 0121 12c0 .778-.099 1.533-.284 2.253m0 0A17.919 17.919 0 0112 16.5c-3.162 0-6.133-.815-8.716-2.247m0 0A9.015 9.015 0 013 12c0-1.605.42-3.113 1.157-4.418" />
                            </svg>
                        </div>
                        <h4 className="text-4xl font-bold text-gray-900 mb-2">75+</h4>
                        <p className="text-sm font-semibold text-gray-500 uppercase tracking-widest">
                            Languages<br />Supported
                        </p>
                    </div>

                    {/* 4. Bottom Middle: Yellow CTA */}
                    <div className="md:col-span-4 bg-[#FFC20E] rounded-[40px] p-8 flex flex-col justify-center relative shadow-lg group hover:shadow-xl hover:-translate-y-1 transition-all cursor-pointer min-h-[280px]">
                        <h3 className="text-xl font-bold text-gray-900 mb-8 leading-tight">
                            Get Your Quotation For<br />Dubbing Today!
                        </h3>
                        <button
                            onClick={() => navigate('/input')}
                            className="bg-black text-white text-[10px] font-bold px-6 py-3 rounded-full w-fit flex items-center gap-2 group-hover:bg-gray-800 transition-colors uppercase tracking-widest">
                            Let's Talk
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={3} stroke="currentColor" className="w-3 h-3 group-hover:translate-x-1 transition-transform">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                            </svg>
                        </button>
                    </div>

                    {/* 5. Bottom Right: Purple Ribbed */}
                    <div className="md:col-span-4 bg-[#8B5CF6] rounded-[40px] relative overflow-hidden min-h-[280px] hover:-translate-y-1 transition-transform duration-500">
                        <div className="absolute inset-0 bg-gradient-to-br from-[#7C3AED] to-[#6D28D9]"></div>
                        <img
                            src={purpleRibbed}
                            alt="Purple Ribbed"
                            className="relative z-10 w-full h-full object-cover opacity-90 mix-blend-plus-lighter"
                        />
                    </div>

                </div>
            </div>
        </section>
    );
};

export default HeroSection;
