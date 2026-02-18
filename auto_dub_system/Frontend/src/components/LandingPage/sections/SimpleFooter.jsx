import React from 'react';

const SimpleFooter = () => {
    return (
        <footer className="bg-white py-10 px-6 max-w-7xl mx-auto border-t border-gray-100">
            <div className="flex flex-col md:flex-row justify-between items-center text-sm font-medium text-gray-500">
                <p>© 2024 AUTODUB. All rights reserved.</p>
                <div className="flex gap-6 mt-4 md:mt-0">
                    <p className="cursor-pointer hover:text-purple-600 transition-colors">Instagram</p>
                    <p className="cursor-pointer hover:text-purple-600 transition-colors">Twitter</p>
                    <p className="cursor-pointer hover:text-purple-600 transition-colors">LinkedIn</p>
                </div>
            </div>
        </footer>
    );
};

export default SimpleFooter;
