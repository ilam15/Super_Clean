import React, { useState } from 'react';

const AIDubbingSection = () => {
    const [activeTab, setActiveTab] = useState('English');

    const tabs = ['English', 'Spanish', 'Hindi'];

    // Placeholder content for demo - normally would be video URLs
    const content = {
        'English': { title: "Original Content", text: "Experience the original clarity and emotion.", color: "bg-blue-500" },
        'Spanish': { title: "Spanish Dub", text: "Fluidez natural y sincronización perfecta.", color: "bg-orange-500" },
        'Hindi': { title: "Hindi Dub", text: "प्रामाणिक भावनाएं और सटीक अनुवाद।", color: "bg-green-500" }
    };

    return (
        <section className="py-20 px-6 max-w-7xl mx-auto">
            <div className="flex flex-col md:flex-row justify-between items-end mb-12">
                <div className="max-w-xl">
                    <h2 className="text-4xl md:text-5xl font-bold mb-6 leading-tight">
                        Best AI Dubbing for video and content localization
                    </h2>
                    <p className="text-gray-500 font-medium">
                        Seamlessly transform your videos into any language with our advanced AI.
                        Click below to hear the difference.
                    </p>
                </div>
                <button className="hidden md:flex bg-transparent border border-gray-200 text-black px-6 py-3 rounded-full items-center gap-2 hover:bg-black hover:text-white transition-all text-xs font-bold tracking-widest uppercase">
                    View All
                    <span className="text-lg">→</span>
                </button>
            </div>

            {/* Interactive Area */}
            <div className="bg-gray-100 rounded-[40px] p-2 md:p-4">
                {/* Tabs */}
                <div className="flex flex-wrap gap-2 mb-4 bg-white p-2 rounded-[30px] w-fit mx-auto md:mx-0 shadow-sm">
                    {tabs.map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-6 py-2 rounded-full text-sm font-bold transition-all duration-300 ${activeTab === tab
                                    ? 'bg-black text-white shadow-md'
                                    : 'bg-transparent text-gray-500 hover:bg-gray-50'
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Display Area (Mock Video Player) */}
                <div className={`w-full aspect-video rounded-[30px] ${content[activeTab].color} transition-colors duration-500 flex flex-col items-center justify-center text-white relative overflow-hidden group`}>
                    <div className="absolute inset-0 bg-black/20 group-hover:bg-black/10 transition-colors"></div>

                    <div className="w-20 h-20 bg-white/30 backdrop-blur-sm rounded-full flex items-center justify-center cursor-pointer hover:scale-110 transition-transform">
                        <svg className="w-8 h-8 text-white fill-current ml-1" viewBox="0 0 24 24">
                            <path d="M8 5v14l11-7z" />
                        </svg>
                    </div>

                    <h3 className="mt-8 text-2xl font-bold relative z-10">{content[activeTab].title}</h3>
                    <p className="text-lg opacity-90 relative z-10">{content[activeTab].text}</p>
                </div>
            </div>

            <div className="mt-8 md:hidden text-center">
                <button className="bg-transparent border border-gray-200 text-black px-6 py-3 rounded-full items-center gap-2 hover:bg-black hover:text-white transition-all text-xs font-bold tracking-widest uppercase inline-flex">
                    View All
                    <span className="text-lg">→</span>
                </button>
            </div>
        </section>
    );
};

export default AIDubbingSection;
