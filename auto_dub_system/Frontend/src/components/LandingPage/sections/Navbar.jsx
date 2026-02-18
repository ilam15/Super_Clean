import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const Navbar = () => {
    const [scrolled, setScrolled] = useState(false);

    useEffect(() => {
        const handleScroll = () => {
            setScrolled(window.scrollY > 20);
        };
        window.addEventListener('scroll', handleScroll);
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const navigate = useNavigate();

    return (
        <nav className="sticky top-0 left-0 right-0 z-50 bg-white py-4 transition-all duration-300">
            <div className="max-w-7xl mx-auto px-6 flex items-center justify-between">
                <div className="flex items-center gap-2 cursor-pointer" onClick={() => navigate('/')}>
                    <div className="bg-black text-white p-1 rounded-sm font-bold text-xl h-8 w-8 flex items-center justify-center">A</div>
                    <span className="font-bold text-xl tracking-wide">UTODUB</span>
                </div>

                <ul className="hidden md:flex items-center gap-8 text-xs font-bold text-gray-800 tracking-widest">
                    {['HOME', 'CONVERT', 'DOWNLOAD'].map((item) => (
                        <li key={item}
                            onClick={() => {
                                if (item === 'HOME') navigate('/');
                                if (item === 'CONVERT') navigate('/input');
                                if (item === 'DOWNLOAD') navigate('/preview');
                            }}
                            className="cursor-pointer hover:text-purple-600 transition-colors relative group">
                            {item}
                            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-purple-600 transition-all duration-300 group-hover:w-full"></span>
                        </li>
                    ))}
                </ul>

                <div className="flex gap-4">
                    <button
                        onClick={() => navigate('/login')}
                        className="bg-black text-white text-xs font-bold px-6 py-3 rounded-full flex items-center gap-2 hover:bg-gray-800 transition-colors cursor-pointer tracking-wider hover:scale-105 active:scale-95 duration-300">
                        SIGN-IN
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                        </svg>
                    </button>
                </div>
            </div>
        </nav>
    );
};

export default Navbar;
