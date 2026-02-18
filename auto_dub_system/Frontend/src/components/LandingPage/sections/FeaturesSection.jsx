import React from 'react';

const FeaturesSection = () => {
    const features = [
        {
            title: "Precision Dubbing",
            description: "Lip-syncing that looks as natural as the original, ensuring viewers forget it's dubbed.",
            icon: "🎯", // Placeholder icons, ideally SVGs
            color: "bg-blue-100"
        },
        {
            title: "Flexible Solutions",
            description: "From automated AI dubbing to human-verified professional quality, we scale to your needs.",
            icon: "⚙️",
            color: "bg-purple-100"
        },
        {
            title: "High Quality",
            description: "Crystal clear audio engineering and professional voice clones that maintain emotional depth.",
            icon: "✨",
            color: "bg-pink-100"
        }
    ];

    return (
        <section className="py-20 px-6 max-w-7xl mx-auto bg-[#F7F7FA] rounded-[50px] my-10">
            <div className="text-center mb-16">
                <h2 className="text-4xl md:text-5xl font-bold mb-4">We Perfect Global Communication</h2>
                <p className="text-gray-500 max-w-2xl mx-auto">Bridging language barriers with technology and art.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {features.map((feature, index) => (
                    <div key={index} className={`p-8 rounded-[30px] hover:shadow-lg transition-shadow duration-300 bg-white border border-gray-100`}>
                        <div className={`w-16 h-16 rounded-full ${feature.color} flex items-center justify-center text-3xl mb-6`}>
                            {feature.icon}
                        </div>
                        <h3 className="text-2xl font-bold mb-4">{feature.title}</h3>
                        <p className="text-gray-500 leading-relaxed font-medium text-sm">
                            {feature.description}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default FeaturesSection;
