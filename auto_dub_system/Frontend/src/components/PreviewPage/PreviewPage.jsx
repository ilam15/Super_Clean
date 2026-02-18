import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
// import axios from 'axios'; // Keeping axios import as requested, even if unused for now

const PreviewPage = () => {
    const location = useLocation();
    const state = location.state || {}; // Fallback to empty object if no state

    const initialMetadata = state.metadata || {
        originalLanguage: 'Spanish',
        dubbedLanguage: 'English',
        duration: '3:45',
        resolution: '1080p',
        status: 'Synced Successfully',
    };

    const videoUrls = {
        original: state.originalVideoUrl || 'https://www.w3schools.com/html/mov_bbb.mp4',
        dubbed: state.videoUrl || 'https://www.w3schools.com/html/movie.mp4'
    };
    // State Management
    const [isDubbed, setIsDubbed] = useState(true);
    const [isPlaying, setIsPlaying] = useState(false);
    const [metadata, setMetadata] = useState(initialMetadata);
    const [pageLoaded, setPageLoaded] = useState(false); // For fade-in animation
    const [videoLoading, setVideoLoading] = useState(false); // For video buffering state
    const [toast, setToast] = useState({ show: false, message: '', type: 'success' }); // For notifications

    const videoRef = useRef(null);

    // Fade-in effect on mount
    useEffect(() => {
        setPageLoaded(true);
    }, []);

    // Toggle Video Source with loading state
    const handleToggle = (dubbed) => {
        if (isDubbed === dubbed) return; // No change

        setVideoLoading(true); // Start loading spinner
        setIsDubbed(dubbed);
        setIsPlaying(false);

        if (videoRef.current) {
            videoRef.current.pause();
            videoRef.current.load();
        }

        // Simulate a short loading delay for effect (or real buffering)
        setTimeout(() => setVideoLoading(false), 500);
    };

    const handleVideoPlay = () => setIsPlaying(true);
    const handleVideoPause = () => setIsPlaying(false);

    // Toast Notification Logic
    const showToastMessage = (message, type = 'success') => {
        setToast({ show: true, message, type });
        setTimeout(() => setToast({ ...toast, show: false }), 3000); // Hide after 3s
    };

    // User Action Handlers
    const handleDownload = async () => {
        if (!videoUrls.dubbed) {
            showToastMessage('No video available for download.', 'error');
            return;
        }

        try {
            showToastMessage('Download started! 📥');

            const response = await fetch(videoUrls.dubbed);
            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            const link = document.createElement('a');
            link.href = url;
            link.download = `dubbed_video_${Date.now()}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            window.URL.revokeObjectURL(url);

        } catch (error) {
            console.error('Download error:', error);
            // Fallback to direct link if fetch fails (e.g. CORS on placeholder)
            const link = document.createElement('a');
            link.href = videoUrls.dubbed;
            link.download = `dubbed_video_${Date.now()}.mp4`;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const navigate = useNavigate();

    const handleBack = () => {
        console.log('Going back...');
        navigate('/input');
    };

    const handleSubmit = () => {
        showToastMessage('Published successfully! 🚀');
        console.log('Submitting...');
    };

    return (
        <div className={`min-h-screen bg-gradient-to-br from-gray-50 to-white text-gray-900 font-sans selection:bg-purple-100 selection:text-purple-900 transition-opacity duration-700 ${pageLoaded ? 'opacity-100' : 'opacity-0'}`}>

            {/* Toast Notification */}
            <div className={`fixed top-5 right-5 z-50 transform transition-all duration-500 ease-in-out ${toast.show ? 'translate-y-0 opacity-100' : '-translate-y-10 opacity-0 pointer-events-none'}`}>
                <div className="bg-white border-l-4 border-purple-600 rounded shadow-2xl px-6 py-4 flex items-center">
                    <span className="text-purple-600 mr-2 text-xl">✨</span>
                    <p className="font-semibold text-gray-800">{toast.message}</p>
                </div>
            </div>

            <main className="max-w-7xl mx-auto px-4 md:px-8 py-12">

                {/* Header Section with Animation */}
                <div className="text-center mb-12 max-w-3xl mx-auto animate-fade-in-down">
                    <div className="inline-block px-4 py-1.5 mb-6 text-xs font-bold tracking-widest text-purple-600 uppercase bg-purple-100 rounded-full">
                        Final Step
                    </div>
                    <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-gray-900 mb-4 leading-tight">
                        Preview Your <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-600 via-blue-500 to-purple-600 bg-300% animate-gradient">Masterpiece</span>
                    </h1>
                    <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto">
                        Your video has been successfully dubbed and synchronized. Review the results below before downloading or sharing.
                    </p>
                </div>

                {/* Main Content Grid */}
                <div className="grid lg:grid-cols-12 gap-8 lg:gap-12 items-start">

                    {/* Left Column: Video Player */}
                    <div className="lg:col-span-8 flex flex-col space-y-6">

                        {/* Video Container with visual polish */}
                        <div className={`video-container relative bg-black rounded-3xl p-1 shadow-2xl transition-all duration-500 transform ${isPlaying ? 'scale-[1.01] shadow-purple-200 ring-4 ring-purple-100' : 'hover:scale-[1.005]'}`}>
                            <div className="relative rounded-2xl overflow-hidden bg-black aspect-video group">

                                {/* Loading Spinner Overlay */}
                                {videoLoading && (
                                    <div className="absolute inset-0 flex items-center justify-center z-20 bg-black/60 backdrop-blur-sm">
                                        <div className="w-12 h-12 border-4 border-purple-500 border-t-transparent rounded-full animate-spin"></div>
                                    </div>
                                )}

                                <video
                                    ref={videoRef}
                                    className="w-full h-full object-contain"
                                    controls
                                    src={isDubbed ? videoUrls.dubbed : videoUrls.original}
                                    onPlay={handleVideoPlay}
                                    onPause={handleVideoPause}
                                    onWaiting={() => setVideoLoading(true)}
                                    onCanPlay={() => setVideoLoading(false)}
                                >
                                    Your browser does not support the video tag.
                                </video>
                            </div>
                        </div>

                        {/* Animated Toggle Controls */}
                        <div className="flex justify-center">
                            <div className="bg-gray-100 p-1.5 rounded-full inline-flex relative shadow-inner">
                                {/* Sliding Background for Toggle */}
                                <div
                                    className={`absolute top-1.5 bottom-1.5 w-1/2 rounded-full bg-white shadow-md transition-all duration-300 ease-out transform ${isDubbed ? 'translate-x-[96%]' : 'translate-x-0'}`}
                                ></div>

                                <button
                                    onClick={() => handleToggle(false)}
                                    className={`relative z-10 w-32 py-2.5 rounded-full text-sm font-bold transition-colors duration-300 ${!isDubbed ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Original
                                </button>
                                <button
                                    onClick={() => handleToggle(true)}
                                    className={`relative z-10 w-32 py-2.5 rounded-full text-sm font-bold transition-colors duration-300 ${isDubbed ? 'text-gray-900' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Dubbed
                                </button>
                            </div>
                        </div>


                    </div>

                    {/* Right Column: Details & Actions */}
                    <div className="lg:col-span-4 flex flex-col gap-6">

                        {/* Metadata Card */}
                        <div className="bg-white/80 backdrop-blur-md rounded-3xl border border-gray-100 p-6 shadow-xl shadow-gray-100/50 hover:shadow-2xl hover:shadow-purple-100/50 transition-all duration-500">
                            <div className="flex items-center space-x-4 mb-8">
                                <div className={`p-3 rounded-2xl ${metadata.status.includes('Success') ? 'bg-green-100 text-green-600' : 'bg-yellow-100 text-yellow-600'}`}>
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                                </div>
                                <div>
                                    <h3 className="font-bold text-gray-900 text-lg">Dubbing Complete</h3>
                                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Ready for download</p>
                                </div>
                            </div>

                            <div className="space-y-5">
                                <div className="flex items-center justify-between group">
                                    <div className="flex items-center space-x-3 text-gray-500 group-hover:text-purple-600 transition-colors">
                                        <span className="text-xl">🎬</span>
                                        <span className="text-sm font-medium">Source Language</span>
                                    </div>
                                    <span className="text-sm font-bold text-gray-900">{metadata.originalLanguage}</span>
                                </div>
                                <div className="flex items-center justify-between group">
                                    <div className="flex items-center space-x-3 text-gray-500 group-hover:text-purple-600 transition-colors">
                                        <span className="text-xl">🗣️</span>
                                        <span className="text-sm font-medium">Target Language</span>
                                    </div>
                                    <span className="text-sm font-bold text-purple-600 bg-purple-50 px-3 py-1 rounded-full border border-purple-100">{metadata.dubbedLanguage}</span>
                                </div>
                                <div className="flex items-center justify-between group">
                                    <div className="flex items-center space-x-3 text-gray-500 group-hover:text-purple-600 transition-colors">
                                        <span className="text-xl">🕒</span>
                                        <span className="text-sm font-medium">Duration</span>
                                    </div>
                                    <span className="text-sm font-bold text-gray-900">{metadata.duration}</span>
                                </div>
                                <div className="flex items-center justify-between group">
                                    <div className="flex items-center space-x-3 text-gray-500 group-hover:text-purple-600 transition-colors">
                                        <span className="text-xl">🔊</span>
                                        <span className="text-sm font-medium">Lip-Sync</span>
                                    </div>
                                    <span className="text-sm font-bold text-green-600 flex items-center">
                                        {metadata.status}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Actions Section */}
                        <div className="space-y-4">
                            <button
                                onClick={handleDownload}
                                className="w-full group relative flex justify-center items-center py-4 px-6 border border-transparent text-base font-bold rounded-2xl text-white bg-gray-900 hover:bg-gray-800 transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-900 overflow-hidden"
                            >
                                <span className="absolute inset-0 w-full h-full bg-gradient-to-r from-gray-800 to-gray-900 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></span>
                                <svg className="w-5 h-5 mr-3 relative z-10 group-hover:animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
                                <span className="relative z-10">Download Video</span>
                            </button>

                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={handleBack}
                                    className="flex justify-center items-center py-3.5 px-4 border-2 border-gray-100 text-sm font-bold rounded-2xl text-gray-600 bg-white hover:bg-gray-50 hover:border-gray-200 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-200 transition-all duration-300"
                                >
                                    Go Back
                                </button>
                                <button
                                    onClick={handleSubmit}
                                    className="flex justify-center items-center py-3.5 px-4 border border-transparent text-sm font-bold rounded-2xl text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 transition-all duration-300 transform hover:-translate-y-1 hover:shadow-lg shadow-purple-200"
                                >
                                    Publish
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default PreviewPage;
