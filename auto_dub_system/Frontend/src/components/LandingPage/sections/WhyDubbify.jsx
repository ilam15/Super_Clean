import React from 'react';
import abstractWaves from '../../../assets/abstract_waves.png'; // Reusing existing asset for now

const WhyDubbify = () => {
    return (
        <section className="py-20 px-6 max-w-7xl mx-auto">
            <div className="bg-black rounded-[50px] overflow-hidden text-white grid grid-cols-1 md:grid-cols-2">
                <div className="p-12 md:p-20 flex flex-col justify-center">
                    <h2 className="text-4xl md:text-5xl font-bold mb-8 leading-tight">Why Choose Dubbify?</h2>
                    <ul className="flex flex-col gap-6">
                        {[
                            'State-of-the-art AI Models',
                            'Human-in-the-loop Verification',
                            'Fast Turnaround Times',
                            'Enterprise Security Standards'
                        ].map((item, i) => (
                            <li key={i} className="flex items-center gap-4 text-lg font-medium text-gray-300">
                                <span className="w-8 h-8 rounded-full bg-white/20 flex items-center justify-center text-white">✓</span>
                                {item}
                            </li>
                        ))}
                    </ul>
                    <button className="mt-12 bg-white text-black px-8 py-4 rounded-full font-bold w-fit hover:bg-gray-200 transition-colors">
                        GET PROPOSAL
                    </button>
                </div>

                <div className="relative h-[400px] md:h-auto">
                    <img
                        src={abstractWaves}
                        alt="Why Dubbify"
                        className="absolute inset-0 w-full h-full object-cover opacity-80"
                    />
                    <div className="absolute inset-0 bg-gradient-to-r from-black via-black/50 to-transparent"></div>
                </div>
            </div>
        </section>
    );
};

export default WhyDubbify;
