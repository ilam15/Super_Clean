import React from 'react';

const Footer = () => {
    return (
        <footer className="bg-white pt-20 pb-10 px-6 max-w-7xl mx-auto border-t border-gray-100 mt-20">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-12 mb-20">
                <div className="col-span-1 md:col-span-2">
                    <h2 className="text-4xl font-bold mb-6">See how we can help your business grow</h2>
                    <button className="bg-black text-white px-8 py-4 rounded-full text-sm font-bold tracking-widest hover:bg-gray-800 transition-transform hover:-translate-y-1 inline-flex items-center gap-2">
                        LET'S TALK
                        <span className="text-xl">↗</span>
                    </button>
                </div>

                <div className="flex flex-col gap-4">
                    <h4 className="font-bold text-gray-400 text-xs tracking-widest uppercase mb-4">Company</h4>
                    {['About Us', 'Careers', 'Blog', 'Contact'].map(link => (
                        <a key={link} href="#" className="font-semibold hover:text-purple-600 transition-colors">{link}</a>
                    ))}
                </div>

                <div className="flex flex-col gap-4">
                    <h4 className="font-bold text-gray-400 text-xs tracking-widest uppercase mb-4">Legal</h4>
                    {['Terms', 'Privacy', 'Cookies'].map(link => (
                        <a key={link} href="#" className="font-semibold hover:text-purple-600 transition-colors">{link}</a>
                    ))}
                </div>
            </div>
        </footer>
    );
};

export default Footer;
