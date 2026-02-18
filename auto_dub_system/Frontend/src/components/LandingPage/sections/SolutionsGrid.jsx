import React from 'react';

const SolutionsGrid = () => {
    const solutions = [
        { title: "Subject & Context Awareness", desc: "AI that understands the context of your video for accurate emotional tone.", color: "bg-purple-50" },
        { title: "Precision Syncing", desc: "Lip-sync technology that matches the dubbed audio to the speaker's mouth movements.", color: "bg-blue-50" },
        { title: "Emotional Tone", desc: "Preserves the original speaker's emotional delivery and intent.", color: "bg-green-50" },
        { title: "Background Noise Removal", desc: "Cleans up audio tracks for professional studio quality sound.", color: "bg-red-50" },
        { title: "Multi-Speaker Detection", desc: "Separates and dubs multiple speakers distinctly.", color: "bg-yellow-50" },
        { title: "Custom Voice Clones", desc: "Create a digital twin of your own voice for branding.", color: "bg-indigo-50" },
        { title: "Subtitle Generation", desc: "Auto-generated accurate subtitles in target languages.", color: "bg-pink-50" },
        { title: "Global Reach", desc: "Scale to 50+ languages instantly.", color: "bg-teal-50" }
    ];

    return (
        <section className="py-20 px-6 max-w-7xl mx-auto">
            <div className="text-center mb-16">
                <h2 className="text-4xl md:text-5xl font-bold mb-4">Specialized Solutions</h2>
                <p className="text-gray-500 max-w-2xl mx-auto">Tailored features for every content creator.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {solutions.map((sol, idx) => (
                    <div key={idx} className={`p-8 rounded-[30px] ${sol.color} hover:scale-105 transition-transform duration-300 border border-black/5`}>
                        <h3 className="text-xl font-bold mb-3">{sol.title}</h3>
                        <p className="text-sm text-gray-600 leading-relaxed">
                            {sol.desc}
                        </p>
                    </div>
                ))}
            </div>
        </section>
    );
};

export default SolutionsGrid;
