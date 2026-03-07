import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const PreviewPage = () => {
    const location = useLocation();
    const state = location.state || {};

    const initialMetadata = state.metadata || {
        originalLanguage: 'Spanish',
        dubbedLanguage: 'English',
        duration: '3:45',
        resolution: '1080p',
        status: 'Synced Successfully',
        transcript: [
            { speaker_no: 'SPEAKER_00', start_time: 0.0, end_time: 3.2, text: 'Welcome to the auto-dubbing demo.' },
            { speaker_no: 'SPEAKER_01', start_time: 3.5, end_time: 7.1, text: 'This system translates speech in real time.' },
            { speaker_no: 'SPEAKER_00', start_time: 7.4, end_time: 11.8, text: 'You can review and edit the transcript here.' },
            { speaker_no: 'SPEAKER_01', start_time: 12.0, end_time: 15.5, text: 'Then download the final dubbed video.' },
        ],
    };

    const videoUrls = {
        original: state.originalVideoUrl || 'https://www.w3schools.com/html/mov_bbb.mp4',
        dubbed: state.videoUrl || 'https://www.w3schools.com/html/movie.mp4'
    };
    // downloadUrl is the S3 presigned URL if available, else same as videoUrls.dubbed
    const downloadUrl = state.downloadUrl || videoUrls.dubbed;

    // ── Core State ──────────────────────────────────────────────────
    const [isDubbed, setIsDubbed] = useState(true);
    const [isPlaying, setIsPlaying] = useState(false);
    const [metadata, setMetadata] = useState(initialMetadata);
    const [pageLoaded, setPageLoaded] = useState(false);
    const [videoLoading, setVideoLoading] = useState(false);
    const [toast, setToast] = useState({ show: false, message: '', type: 'success' });

    // ── Transcript State ─────────────────────────────────────────────
    const [transcript, setTranscript] = useState(initialMetadata.transcript || []);
    const [isEditMode, setIsEditMode] = useState(false);
    const [editingIdx, setEditingIdx] = useState(null);
    const [editDraft, setEditDraft] = useState('');
    const [transcriptExpanded, setTranscriptExpanded] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [savedSnapshot, setSavedSnapshot] = useState(null); // for discard
    const [copiedAll, setCopiedAll] = useState(false);
    const [copiedLink, setCopiedLink] = useState(false);

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
    const handleDownload = () => {
        if (!downloadUrl) {
            showToastMessage('No video available for download.', 'error');
            return;
        }
        // Use window.open — the presigned URL has Content-Disposition: attachment
        // so the browser downloads instead of streaming
        showToastMessage('Download started! 📥');
        window.open(downloadUrl, '_blank');
    };

    const handleCopyLink = () => {
        if (!downloadUrl) {
            showToastMessage('No link available to copy.', 'error');
            return;
        }
        navigator.clipboard.writeText(downloadUrl)
            .then(() => {
                setCopiedLink(true);
                showToastMessage('Link copied to clipboard! 🔗');
                setTimeout(() => setCopiedLink(false), 2000);
            })
            .catch(() => {
                // Fallback for browsers that block clipboard without HTTPS
                const ta = document.createElement('textarea');
                ta.value = downloadUrl;
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                setCopiedLink(true);
                showToastMessage('Link copied! 🔗');
                setTimeout(() => setCopiedLink(false), 2000);
            });
    };

    const navigate = useNavigate();

    // Derived: filtered transcript for segment count subtitle
    const filteredTranscript = searchQuery
        ? transcript.filter(t =>
            t.text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            t.speaker_no?.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : transcript;

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

                        {/* ═══ Generated Transcript ═══ */}
                        {transcript.length > 0 && (
                            <div className="bg-white rounded-3xl shadow-xl shadow-gray-100/50 border border-gray-100 mt-4 transition-all duration-500 hover:shadow-2xl hover:shadow-purple-100/50 overflow-hidden">

                                {/* ── Header Bar ── */}
                                <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-purple-50/60 to-indigo-50/40">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-xl bg-purple-100 flex items-center justify-center text-purple-600 text-lg">📝</div>
                                        <div>
                                            <h3 className="font-bold text-gray-900 text-base leading-tight">Generated Transcript</h3>
                                            <p className="text-xs text-gray-400 font-medium">{transcript.length} segments{searchQuery && ` · ${filteredTranscript.length} matches`}</p>
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        {/* Copy All */}
                                        <button
                                            onClick={() => {
                                                const text = transcript.map(t => `[${t.speaker_no?.replace('SPEAKER_', 'Speaker ')}] ${t.text}`).join('\n');
                                                navigator.clipboard.writeText(text).then(() => {
                                                    setCopiedAll(true);
                                                    setTimeout(() => setCopiedAll(false), 2000);
                                                });
                                            }}
                                            title="Copy all transcript"
                                            className="p-2 rounded-xl text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200"
                                        >
                                            {copiedAll
                                                ? <svg className="w-4 h-4 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" /></svg>
                                                : <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-4 10h6a2 2 0 002-2v-8a2 2 0 00-2-2h-6a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>
                                            }
                                        </button>

                                        {/* Edit Mode Toggle */}
                                        <button
                                            onClick={() => {
                                                if (!isEditMode) {
                                                    setSavedSnapshot(JSON.parse(JSON.stringify(transcript)));
                                                    setIsEditMode(true);
                                                    setTranscriptExpanded(true);
                                                } else {
                                                    // Save & exit
                                                    setIsEditMode(false);
                                                    setEditingIdx(null);
                                                    showToastMessage('Transcript saved ✅');
                                                }
                                            }}
                                            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-300 ${isEditMode
                                                ? 'bg-green-100 text-green-700 hover:bg-green-200 ring-1 ring-green-300'
                                                : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                                                }`}
                                        >
                                            {isEditMode
                                                ? <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" /></svg>Save All</>
                                                : <><svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>Edit</>
                                            }
                                        </button>

                                        {/* Discard button (only in edit mode) */}
                                        {isEditMode && (
                                            <button
                                                onClick={() => {
                                                    if (savedSnapshot) setTranscript(savedSnapshot);
                                                    setIsEditMode(false);
                                                    setEditingIdx(null);
                                                    showToastMessage('Changes discarded', 'error');
                                                }}
                                                className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-red-50 text-red-500 hover:bg-red-100 transition-all duration-200 ring-1 ring-red-200"
                                            >
                                                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                                                Discard
                                            </button>
                                        )}

                                        {/* Expand / Collapse */}
                                        <button
                                            onClick={() => setTranscriptExpanded(p => !p)}
                                            className="p-2 rounded-xl text-gray-400 hover:text-purple-600 hover:bg-purple-50 transition-all duration-200"
                                        >
                                            <svg className={`w-4 h-4 transition-transform duration-300 ${transcriptExpanded ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" /></svg>
                                        </button>
                                    </div>
                                </div>

                                {/* ── Search Bar (visible when expanded) ── */}
                                {transcriptExpanded && (
                                    <div className="px-6 pt-4">
                                        <div className="relative">
                                            <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z" /></svg>
                                            <input
                                                type="text"
                                                value={searchQuery}
                                                onChange={e => setSearchQuery(e.target.value)}
                                                placeholder="Search transcript…"
                                                className="w-full pl-9 pr-4 py-2 text-sm rounded-xl border border-gray-200 bg-gray-50 focus:outline-none focus:ring-2 focus:ring-purple-300 focus:border-purple-300 placeholder-gray-300 transition-all duration-200"
                                            />
                                            {searchQuery && (
                                                <button onClick={() => setSearchQuery('')} className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-300 hover:text-gray-500">
                                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* ── Segments List ── */}
                                <div className={`transition-all duration-500 overflow-hidden ${transcriptExpanded ? 'max-h-[480px]' : 'max-h-0'}`}>
                                    <div className="px-6 pb-6 pt-3 space-y-2.5 overflow-y-auto max-h-[420px] custom-scrollbar">
                                        {(() => {
                                            const filtered = searchQuery
                                                ? transcript.filter(t =>
                                                    t.text?.toLowerCase().includes(searchQuery.toLowerCase()) ||
                                                    t.speaker_no?.toLowerCase().includes(searchQuery.toLowerCase())
                                                )
                                                : transcript;

                                            if (filtered.length === 0) {
                                                return (
                                                    <div className="py-8 text-center">
                                                        <p className="text-gray-400 text-sm">No segments match your search.</p>
                                                    </div>
                                                );
                                            }

                                            return filtered.map((item, idx) => {
                                                const realIdx = transcript.indexOf(item);
                                                const isEditing = editingIdx === realIdx;
                                                const speakerColors = [
                                                    'bg-purple-100 text-purple-700',
                                                    'bg-blue-100 text-blue-700',
                                                    'bg-teal-100 text-teal-700',
                                                    'bg-orange-100 text-orange-700',
                                                ];
                                                const speakerNum = parseInt(item.speaker_no?.replace('SPEAKER_', '') || '0', 10);
                                                const colorClass = speakerColors[speakerNum % speakerColors.length];

                                                return (
                                                    <div
                                                        key={realIdx}
                                                        className={`rounded-2xl border transition-all duration-300 ${isEditing
                                                            ? 'border-purple-300 bg-purple-50/60 shadow-md shadow-purple-100'
                                                            : 'border-gray-100 bg-gray-50/70 hover:border-purple-200 hover:bg-purple-50/40'
                                                            }`}
                                                    >
                                                        {/* Segment Header */}
                                                        <div className="flex items-center justify-between px-4 pt-3 pb-2">
                                                            <div className="flex items-center gap-2">
                                                                <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full tracking-wide ${colorClass}`}>
                                                                    {item.speaker_no?.replace('SPEAKER_', 'Speaker ') || 'Speaker'}
                                                                </span>
                                                                <span className="text-xs text-gray-400 font-mono">
                                                                    {item.start_time?.toFixed(1)}s – {item.end_time?.toFixed(1)}s
                                                                </span>
                                                            </div>
                                                            {/* Per-segment Edit / Save / Cancel */}
                                                            {isEditMode && (
                                                                <div className="flex items-center gap-1.5">
                                                                    {isEditing ? (
                                                                        <>
                                                                            <button
                                                                                onClick={() => {
                                                                                    const updated = [...transcript];
                                                                                    updated[realIdx] = { ...updated[realIdx], text: editDraft };
                                                                                    setTranscript(updated);
                                                                                    setEditingIdx(null);
                                                                                }}
                                                                                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-green-100 text-green-700 hover:bg-green-200 transition-colors"
                                                                            >
                                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" /></svg>
                                                                                Save
                                                                            </button>
                                                                            <button
                                                                                onClick={() => setEditingIdx(null)}
                                                                                className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-bold bg-gray-100 text-gray-500 hover:bg-gray-200 transition-colors"
                                                                            >
                                                                                <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
                                                                                Cancel
                                                                            </button>
                                                                        </>
                                                                    ) : (
                                                                        <button
                                                                            onClick={() => {
                                                                                setEditingIdx(realIdx);
                                                                                setEditDraft(item.text || '');
                                                                            }}
                                                                            className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold text-purple-600 bg-white border border-purple-200 hover:bg-purple-50 transition-colors"
                                                                        >
                                                                            <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" /></svg>
                                                                            Edit
                                                                        </button>
                                                                    )}
                                                                </div>
                                                            )}
                                                        </div>

                                                        {/* Segment Text */}
                                                        <div className="px-4 pb-3">
                                                            {isEditing ? (
                                                                <div>
                                                                    <textarea
                                                                        autoFocus
                                                                        value={editDraft}
                                                                        onChange={e => setEditDraft(e.target.value)}
                                                                        rows={3}
                                                                        className="w-full text-sm text-gray-800 leading-relaxed bg-white border border-purple-300 rounded-xl px-3 py-2 resize-none focus:outline-none focus:ring-2 focus:ring-purple-400 placeholder-gray-300 transition-all duration-200"
                                                                        placeholder="Enter transcript text…"
                                                                    />
                                                                    <p className="text-right text-xs text-gray-400 mt-1">{editDraft.length} chars</p>
                                                                </div>
                                                            ) : (
                                                                <p className="text-sm text-gray-700 leading-relaxed font-medium">
                                                                    {item.text
                                                                        ? searchQuery
                                                                            ? item.text.split(new RegExp(`(${searchQuery})`, 'gi')).map((part, i) =>
                                                                                part.toLowerCase() === searchQuery.toLowerCase()
                                                                                    ? <mark key={i} className="bg-yellow-200 text-yellow-900 rounded px-0.5">{part}</mark>
                                                                                    : part
                                                                            )
                                                                            : item.text
                                                                        : <span className="text-gray-400 italic">No speech detected</span>
                                                                    }
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                );
                                            });
                                        })()}
                                    </div>
                                </div>

                                {/* ── Footer Status Bar ── */}
                                {isEditMode && (
                                    <div className="px-6 py-3 bg-purple-50/80 border-t border-purple-100 flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
                                        <p className="text-xs text-purple-600 font-semibold">Edit mode active — click <strong>Edit</strong> on any segment to modify its text.</p>
                                    </div>
                                )}
                            </div>
                        )}

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

                            {/* Copy Link Button */}
                            <button
                                onClick={handleCopyLink}
                                className={`w-full flex justify-center items-center py-3.5 px-6 border-2 text-sm font-bold rounded-2xl transition-all duration-300 transform hover:-translate-y-0.5 focus:outline-none focus:ring-2 focus:ring-offset-2 ${copiedLink
                                        ? 'border-green-400 bg-green-50 text-green-700 focus:ring-green-400'
                                        : 'border-purple-200 bg-white text-purple-700 hover:bg-purple-50 hover:border-purple-400 focus:ring-purple-400'
                                    }`}
                            >
                                {copiedLink ? (
                                    <>
                                        <svg className="w-4 h-4 mr-2 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M5 13l4 4L19 7" /></svg>
                                        Copied!
                                    </>
                                ) : (
                                    <>
                                        <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
                                        Copy Link
                                    </>
                                )}
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
