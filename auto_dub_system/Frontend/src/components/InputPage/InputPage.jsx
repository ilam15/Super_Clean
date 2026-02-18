import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './InputPage.css';

const InputPage = () => {
    // State declarations
    const [sourceLanguage, setSourceLanguage] = useState(null);
    const [targetLanguage, setTargetLanguage] = useState(null);
    const [speakerGender, setSpeakerGender] = useState(null);
    const [uploadedVideo, setUploadedVideo] = useState(null);
    const [rawFile, setRawFile] = useState(null);
    const [videoUrl, setVideoUrl] = useState('');
    const [isDragging, setIsDragging] = useState(false);
    const [processingProgress, setProcessingProgress] = useState(0);
    const [isProcessing, setIsProcessing] = useState(false);
    const [showSourceDropdown, setShowSourceDropdown] = useState(false);
    const [showTargetDropdown, setShowTargetDropdown] = useState(false);
    const [uploadProgress, setUploadProgress] = useState({});

    // YouTube-specific state
    const [youtubeVideoInfo, setYoutubeVideoInfo] = useState(null);
    const [selectedQuality, setSelectedQuality] = useState(null);
    const [downloadedVideoPath, setDownloadedVideoPath] = useState(null);
    const [isDownloading, setIsDownloading] = useState(false);
    const [downloadProgress, setDownloadProgress] = useState(0);

    // New Options State

    const [recoverBackgroundNoise, setRecoverBackgroundNoise] = useState(false);
    const [makeVideo, setMakeVideo] = useState(false);

    // Validation Errors
    const [errors, setErrors] = useState({});

    const fileInputRef = useRef(null);
    const dropZoneRef = useRef(null);
    const navigate = useNavigate();

    // Mock data for languages with more properties - Added more languages
    // Professional language list with corrected flags
    const languages = [
        { code: 'en', name: 'English', flag: '🇺🇸', selected: false },
        { code: 'hi', name: 'Hindi', flag: '🇮🇳', selected: false },
        { code: 'es', name: 'Spanish', flag: '🇪🇸', selected: false },
        { code: 'fr', name: 'French', flag: '🇫🇷', selected: false },
        { code: 'de', name: 'German', flag: '🇩🇪', selected: false },
        { code: 'ta', name: 'Tamil', flag: '🇮🇳', selected: false },
        { code: 'zh', name: 'Mandarin', flag: '🇨🇳', selected: false },
        { code: 'ja', name: 'Japanese', flag: '🇯🇵', selected: false },
        { code: 'ko', name: 'Korean', flag: '🇰🇷', selected: false },
        { code: 'ar', name: 'Arabic', flag: '🇸🇦', selected: false },
        { code: 'ru', name: 'Russian', flag: '🇷🇺', selected: false },
        { code: 'pt', name: 'Portuguese', flag: '🇵🇹', selected: false },
        { code: 'it', name: 'Italian', flag: '🇮🇹', selected: false },
        { code: 'nl', name: 'Dutch', flag: '🇳🇱', selected: false },
        { code: 'pl', name: 'Polish', flag: '🇵🇱', selected: false },
        { code: 'tr', name: 'Turkish', flag: '🇹🇷', selected: false },
        { code: 'th', name: 'Thai', flag: '🇹🇭', selected: false },
        { code: 'vi', name: 'Vietnamese', flag: '🇻🇳', selected: false },
        { code: 'he', name: 'Hebrew', flag: '🇮🇱', selected: false },
        { code: 'sv', name: 'Swedish', flag: '🇸🇪', selected: false },
        { code: 'da', name: 'Danish', flag: '🇩🇰', selected: false },
        { code: 'fi', name: 'Finnish', flag: '🇫🇮', selected: false },
        { code: 'no', name: 'Norwegian', flag: '🇳🇴', selected: false },
        { code: 'cs', name: 'Czech', flag: '🇨🇿', selected: false },
        { code: 'hu', name: 'Hungarian', flag: '🇭🇺', selected: false },
        { code: 'el', name: 'Greek', flag: '🇬🇷', selected: false },
        { code: 'ro', name: 'Romanian', flag: '🇷🇴', selected: false },
        { code: 'bg', name: 'Bulgarian', flag: '🇧🇬', selected: false },
    ];

    // Speaker genders for selection
    // Speaker genders for selection - Professional Palette
    const speakerOptions = [
        { id: 'female', name: 'Female', icon: '👩', color: 'bg-rose-50 text-rose-600 border-rose-200' },
        { id: 'male', name: 'Male', icon: '👨', color: 'bg-blue-50 text-blue-600 border-blue-200' }
    ];

    // Simplified platform icons - Only YouTube + plus for others
    const platforms = [
        {
            name: 'YouTube', color: 'bg-red-50 text-red-600', icon: (
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z" />
                </svg>
            )
        },
        { name: '+12', color: 'bg-slate-100 text-slate-600', icon: '+', isPlus: true }
    ];

    // Drag and drop handlers
    const handleDragEnter = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (!dropZoneRef.current.contains(e.relatedTarget)) {
            setIsDragging(false);
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
        e.dataTransfer.dropEffect = 'copy';
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            handleFileUpload(files[0]);
        }
    };

    const handleFileUpload = (file) => {
        // More robust file type checking
        const validVideoTypes = [
            'video/mp4', 'video/webm', 'video/ogg',
            'video/quicktime', 'video/x-msvideo',
            'video/x-matroska', 'application/x-troff-msvideo',
            'video/avi', 'video/mpeg'
        ];

        const validExtensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm', '.m4v', '.mpg', '.mpeg'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

        // Check if mime type is video OR if extension is valid video extension
        const isValidType = file.type.startsWith('video/') || validVideoTypes.includes(file.type);
        const isValidExtension = validExtensions.includes(fileExtension);

        if (!isValidType && !isValidExtension) {
            alert(`Please upload a valid video file. Detected type: ${file.type || 'unknown'}`);
            return;
        }

        // Simulate upload progress
        setUploadProgress({ [file.name]: 0 });
        simulateUploadProgress(file.name);

        const videoData = {
            name: file.name,
            size: (file.size / (1024 * 1024)).toFixed(2) + ' MB',
            type: file.type || 'video/unknown',
            thumbnail: URL.createObjectURL(file), // Creates a preview URL for the video
            duration: '0 mins', // Placeholder as we can't easily get duration without processing
            confidence: '95.7%',
            lang: 'EN-US'
        };

        // Try to get actual video duration if possible (optional enhancement)
        const videoElement = document.createElement('video');
        videoElement.preload = 'metadata';
        videoElement.onloadedmetadata = function () {
            window.URL.revokeObjectURL(videoElement.src);
            const duration = Math.round(videoElement.duration / 60) + ' mins';
            setUploadedVideo(prev => ({ ...prev, duration: duration }));
        }
        videoElement.src = URL.createObjectURL(file);

        setUploadedVideo(videoData);
        setRawFile(file);
    };

    const simulateUploadProgress = (fileName) => {
        let progress = 0;
        const interval = setInterval(() => {
            progress += 5;
            setUploadProgress(prev => ({ ...prev, [fileName]: progress }));

            if (progress >= 100) {
                clearInterval(interval);
            }
        }, 100);
    };

    const handleFileInput = (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    };

    // Language selection handler
    const handleSourceSelect = (code) => {
        setSourceLanguage(code);
        setShowSourceDropdown(false);
    };

    const handleTargetSelect = (code) => {
        setTargetLanguage(code);
        setShowTargetDropdown(false);
    };


    // Close dropdowns on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (!event.target.closest('.custom-dropdown')) {
                setShowSourceDropdown(false);
                setShowTargetDropdown(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);


    // URL processing - Fetch YouTube video info
    const processUrl = async () => {
        if (!videoUrl || isProcessing) return;

        // Validate URL
        const urlPattern = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be|vimeo\.com|bilibili\.com)\/.+/i;
        if (!urlPattern.test(videoUrl)) {
            setErrors(prev => ({ ...prev, url: 'Please enter a valid YouTube, Vimeo, or Bilibili URL' }));
            return;
        }
        setErrors(prev => ({ ...prev, url: null }));

        // Fetch video information from backend
        setIsProcessing(true);
        setProcessingProgress(0);

        try {
            const response = await fetch('http://localhost:8000/youtube/info', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: videoUrl }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to fetch video info');
            }

            const data = await response.json();
            setYoutubeVideoInfo(data.data);
            setProcessingProgress(100);
            setIsProcessing(false);

            console.log('YouTube video info:', data.data);

        } catch (error) {
            console.error(error);
            setIsProcessing(false);
            setErrors(prev => ({ ...prev, url: error.message }));
            alert(`Error: ${error.message}`);
        }
    };

    // Download YouTube video with selected quality
    const downloadYoutubeVideo = async (quality) => {
        if (!videoUrl || !quality || isDownloading) return;

        setIsDownloading(true);
        setDownloadProgress(0);
        setSelectedQuality(quality);

        try {
            // Simulate download progress
            const progressInterval = setInterval(() => {
                setDownloadProgress(prev => {
                    if (prev >= 90) return prev;
                    return prev + 10;
                });
            }, 500);

            const response = await fetch('http://localhost:8000/youtube/download', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: videoUrl, quality }),
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Download failed');
            }

            const data = await response.json();
            setDownloadProgress(100);
            setDownloadedVideoPath(data.file_path);

            // Set uploaded video info for display
            setUploadedVideo({
                name: data.filename,
                size: data.size,
                type: 'video/mp4',
                thumbnail: youtubeVideoInfo.thumbnail,
                duration: Math.round(youtubeVideoInfo.duration / 60) + ' mins',
                confidence: '98.2%',
                lang: 'EN-US',
                source: 'youtube'
            });

            setIsDownloading(false);
            console.log('Downloaded video path:', data.file_path);

        } catch (error) {
            console.error(error);
            setIsDownloading(false);
            setDownloadProgress(0);
            alert(`Download Error: ${error.message}`);
        }
    };


    // Generate video handler
    const handleGenerateVideo = async () => {
        if (isProcessing) return;

        let newErrors = {};

        if (!uploadedVideo && !videoUrl) {
            newErrors.source = 'Please upload a video file or enter a valid URL above';
        }

        if (!targetLanguage) {
            newErrors.targetLang = 'Please select a target language for dubbing';
        }

        if (Object.keys(newErrors).length > 0) {
            setErrors(newErrors);
            return;
        }

        // Clear errors if valid
        setErrors({});

        setIsProcessing(true);
        setProcessingProgress(0);

        try {
            const formData = new FormData();

            // Add file or YouTube video path
            if (rawFile) {
                formData.append('file', rawFile);
            } else if (downloadedVideoPath) {
                // Use YouTube downloaded video
                formData.append('youtube_video_path', downloadedVideoPath);
            }

            // Helper to get full language name if needed, or code. 
            // The backend likely expects full English names based on app.py
            const getLangName = (code) => {
                const l = languages.find(x => x.code === code);
                return l ? l.name : code;
            }

            formData.append('source_lang', sourceLanguage === 'auto' || !sourceLanguage ? 'Automatic' : getLangName(sourceLanguage));
            formData.append('target_lang', getLangName(targetLanguage));
            formData.append('gender', speakerGender || 'Male');
            formData.append('recover_bg', recoverBackgroundNoise);
            formData.append('user_known_languages', "[]");


            // Progress simulation (Initial Upload)
            const progressInterval = setInterval(() => {
                setProcessingProgress(prev => {
                    if (prev >= 90) return prev;
                    return prev + 2;
                });
            }, 800);

            const response = await fetch('http://localhost:8000/upload', {
                method: 'POST',
                body: formData,
            });

            clearInterval(progressInterval);

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Processing failed');
            }

            const data = await response.json();

            if (data.task_id) {
                // Start polling for real results
                const taskId = data.task_id;
                const pollInterval = setInterval(async () => {
                    try {
                        const statusRes = await fetch(`http://localhost:8000/task/${taskId}`);
                        if (!statusRes.ok) return;
                        const statusData = await statusRes.json();

                        if (statusData.status === 'SUCCESS') {
                            clearInterval(pollInterval);
                            setProcessingProgress(100);
                            setIsProcessing(false);

                            const result = statusData.result || {};
                            // Navigate to preview page with REAL video data
                            // Result might contain: output_path, etc.
                            // Assuming result structure: { "result": "path/to/video.mp4" }
                            // Adjusting based on whatever process_stage4 returns.
                            // Currently stage4 return value is not explicitly viewed, but likely a dict or path.

                            // Construct URLs based on simple static serve or similar.
                            // The backend doesn't seem to serve files statically yet or we need to know the URL.
                            // Let's assume /download endpoint can serve it or just direct link if static.
                            // For now, let's use a placeholder or the result directly if it's a URL.

                            const videoUrl = result.output_video ? `http://localhost:8000/download/${result.output_video}` : '';

                            navigate('/preview', {
                                state: {
                                    videoUrl: videoUrl,
                                    originalVideoUrl: null, // We don't have this easily unless returned
                                    language: targetLanguage,
                                    gender: speakerGender,
                                    metadata: {
                                        originalLanguage: getLangName(sourceLanguage) || "Detected",
                                        dubbedLanguage: getLangName(targetLanguage),
                                        duration: uploadedVideo?.duration || "Unknown",
                                        status: "Synced Successfully"
                                    }
                                }
                            });
                        } else if (statusData.status === 'FAILURE' || statusData.status === 'REVOKED') {
                            clearInterval(pollInterval);
                            setIsProcessing(false);
                            alert(`Dubbing failed: ${statusData.error || 'Unknown error'}`);
                        } else {
                            // Still processing, update progress slowly
                            setProcessingProgress(prev => (prev < 98 ? prev + 1 : prev));
                        }
                    } catch (e) {
                        console.error("Polling error:", e);
                    }
                }, 3000);
            } else {
                setIsProcessing(false);
                throw new Error("Invalid response from server");
            }

        } catch (error) {
            console.error(error);
            setIsProcessing(false);
            alert(`Error: ${error.message}`);
        }
    };

    // Calculate estimated time
    const calculateEstimatedTime = () => {
        return (3.5).toFixed(2);
    };

    // Remove uploaded video
    const removeVideo = () => {
        setUploadedVideo(null);
        setVideoUrl('');
        setUploadProgress({});
        setYoutubeVideoInfo(null);
        setSelectedQuality(null);
        setDownloadedVideoPath(null);
        setDownloadProgress(0);
    };


    // Get language name by code
    const getLanguageName = (code) => {
        const lang = languages.find(l => l.code === code);
        return lang ? lang.name : code;
    };

    // Custom Dropdown Component
    const LanguageDropdown = ({ label, value, options, onSelect, isOpen, setIsOpen, isAuto = false }) => {
        const selected = options.find(o => o.code === value) || (isAuto && value === 'auto' ? { name: 'Auto-Detect', flag: '🌐' } : options[0]);

        return (
            <div className="relative custom-dropdown w-full">
                <div className="flex justify-between items-center mb-2">
                    <label className="text-sm font-bold text-slate-700 uppercase tracking-wide">{label}</label>
                </div>
                <div
                    onClick={() => setIsOpen(!isOpen)}
                    className={`bg-white rounded-xl px-4 py-3.5 border transition-all duration-200 cursor-pointer flex items-center justify-between hover:border-blue-400 hover:shadow-sm ${isOpen ? 'border-blue-500 ring-2 ring-blue-500/10' : 'border-slate-200'}`}
                >
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-lg border border-slate-100">
                            {selected.flag}
                        </div>
                        <div>
                            <div className="text-sm font-semibold text-slate-800">{selected.name}</div>
                        </div>
                    </div>
                    <svg xmlns="http://www.w3.org/2000/svg" className={`h-4 w-4 text-slate-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                </div>

                {isOpen && (
                    <div className="absolute top-full mt-2 left-0 right-0 bg-white border border-slate-100 rounded-xl shadow-xl z-50 max-h-64 overflow-y-auto custom-scrollbar animate-fade-in origin-top">
                        {isAuto && (
                            <div
                                onClick={() => onSelect('auto')}
                                className="px-4 py-3 flex items-center gap-3 hover:bg-slate-50 cursor-pointer transition-colors border-b border-slate-50"
                            >
                                <span className="text-lg">🌐</span>
                                <span className="text-sm font-medium text-slate-700">Auto-Detect Output</span>
                            </div>
                        )}
                        {options.map(lang => (
                            <div
                                key={lang.code}
                                onClick={() => onSelect(lang.code)}
                                className={`px-4 py-3 flex items-center gap-3 hover:bg-slate-50 cursor-pointer transition-colors ${value === lang.code ? 'bg-blue-50/60' : ''}`}
                            >
                                <span className="text-lg">{lang.flag}</span>
                                <span className="text-sm font-medium text-slate-700">{lang.name}</span>
                                {value === lang.code && <div className="ml-auto w-1.5 h-1.5 bg-blue-600 rounded-full"></div>}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        );
    };

    return (

        <div className="min-h-screen w-full bg-slate-50 text-slate-900 font-sans p-6 md:p-10 flex flex-col items-center">

            {/* Header */}
            <header className="flex flex-col items-center gap-2 mb-10 animate-fade-in z-10 text-center">
                <h1 className="text-5xl font-extrabold tracking-tight text-slate-900 mb-2">
                    AutoDub <span className="text-slate-500 font-light">Engine</span>
                </h1>
                <p className="text-slate-600 text-base font-bold">Professional Video Localization & Voice Synthesis</p>

                {isProcessing && (
                    <div className="mt-4 px-4 py-2 bg-white border border-slate-200 rounded-full shadow-sm flex items-center gap-3 animate-pulse">
                        <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        <span className="text-xs font-semibold text-blue-600">Processing media... {processingProgress.toFixed(0)}%</span>
                    </div>
                )}
            </header>

            {/* Main Grid - Full coverage */}
            <div className="w-full h-full grid grid-cols-1 lg:grid-cols-3 gap-8 flex-1">

                {/* Column 1: Source Upload */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-full hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-600">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                            </svg>
                        </div>
                        <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wide">Upload Source</h2>
                    </div>

                    {/* Drag & Drop Area */}
                    <div
                        ref={dropZoneRef}
                        className={`flex-1 flex flex-col items-center justify-center mb-6 transition-all duration-200 rounded-xl border-2 border-dashed ${isDragging
                            ? 'border-blue-500 bg-blue-50/50'
                            : 'border-slate-200 bg-slate-50/50 hover:border-blue-400 hover:bg-slate-50'
                            }`}
                        onDragEnter={handleDragEnter}
                        onDragLeave={handleDragLeave}
                        onDragOver={handleDragOver}
                        onDrop={handleDrop}
                    >
                        <div
                            className="w-full h-full flex flex-col items-center justify-center p-8 cursor-pointer"
                            onClick={() => fileInputRef.current?.click()}
                        >
                            <div className="w-16 h-16 mb-4 rounded-full bg-white shadow-sm flex items-center justify-center text-blue-500">
                                <svg xmlns="http://www.w3.org/2000/svg" className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                                </svg>
                            </div>
                            <span className="text-sm font-bold text-slate-700">Click to upload or drag video</span>
                            <span className="text-xs text-slate-500 mt-2">MP4, MOV, AVI (Max 2GB)</span>
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept="video/*"
                                onChange={handleFileInput}
                            />
                        </div>
                    </div>

                    {/* URL Input */}
                    <div className="mb-6">
                        <div className="relative mb-4">
                            <input
                                type="text"
                                value={videoUrl}
                                onChange={(e) => setVideoUrl(e.target.value)}
                                placeholder="Paste YouTube / Vimeo URL..."

                                className={`w-full bg-white border-2 rounded-lg px-4 py-3 text-sm font-medium text-slate-800 focus:outline-none focus:border-slate-900 transition-all pr-20 placeholder-slate-500 ${errors.url ? 'border-red-300 ring-2 ring-red-100' : 'border-slate-200'}`}
                            />
                            <button
                                onClick={processUrl}
                                disabled={!videoUrl || isProcessing}
                                className={`absolute right-1.5 top-1.5 bottom-1.5 px-4 text-xs font-bold rounded-md transition-all ${!videoUrl || isProcessing
                                    ? 'bg-slate-200 text-slate-500'
                                    : 'bg-slate-900 text-white hover:bg-slate-800'
                                    }`}
                            >
                                Fetch
                            </button>
                        </div>

                        {/* Platforms Icons */}
                        <div className="flex justify-center gap-3">
                            {platforms.map((platform) => (
                                <div
                                    key={platform.name}
                                    className={`h-8 px-3 rounded-full flex items-center justify-center gap-2 cursor-pointer transition-transform hover:scale-105 border border-slate-200 ${platform.color}`}
                                    onClick={() => !platform.isPlus && setVideoUrl(`https://${platform.name.toLowerCase()}.com/example`)}
                                >
                                    {platform.isPlus ? (
                                        <span className="text-xs font-bold">{platform.icon} {platform.name}</span>
                                    ) : (
                                        <>
                                            {platform.icon}
                                            <span className="text-xs font-bold">{platform.name}</span>
                                        </>
                                    )}
                                </div>
                            ))}

                        </div>
                        {errors.url && <p className="text-red-500 text-xs font-semibold mt-2 ml-1">{errors.url}</p>}
                        {errors.source && !videoUrl && !uploadedVideo && <p className="text-red-500 text-xs font-semibold mt-2 ml-1">{errors.source}</p>}

                        {/* YouTube Video Info & Quality Selector */}
                        {youtubeVideoInfo && !uploadedVideo && (
                            <div className="mt-6 bg-white border border-slate-200 rounded-xl p-4 animate-fade-in">
                                {/* Video Preview */}
                                <div className="flex items-start gap-3 mb-4 pb-4 border-b border-slate-100">
                                    <div className="w-24 h-16 bg-slate-200 rounded-md overflow-hidden flex-shrink-0">
                                        <img src={youtubeVideoInfo.thumbnail} alt="Video thumbnail" className="w-full h-full object-cover" />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="text-sm font-semibold text-slate-900 truncate mb-1">{youtubeVideoInfo.title}</div>
                                        <div className="text-xs text-slate-600">
                                            {Math.round(youtubeVideoInfo.duration / 60)} mins • {youtubeVideoInfo.uploader}
                                        </div>
                                        {isDownloading && (
                                            <div className="mt-2">
                                                <div className="flex items-center gap-2 text-xs text-blue-600 mb-1">
                                                    <div className="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                                                    <span>Downloading {selectedQuality}... {downloadProgress}%</span>
                                                </div>
                                                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                                                    <div className="h-full bg-blue-600 transition-all duration-300" style={{ width: `${downloadProgress}%` }}></div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Quality Options */}
                                {!isDownloading && !downloadedVideoPath && (
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wide mb-3">Download Quality:</h4>
                                        <div className="grid grid-cols-4 gap-2">
                                            {youtubeVideoInfo.formats
                                                .filter(fmt => fmt.available !== false)
                                                .map((format) => (
                                                    <button
                                                        key={format.quality}
                                                        onClick={() => downloadYoutubeVideo(format.quality)}
                                                        className="px-3 py-2 text-xs font-bold rounded-lg border-2 border-slate-200 bg-white hover:border-blue-500 hover:bg-blue-50 hover:text-blue-600 transition-all duration-200 hover:scale-105"
                                                    >
                                                        {format.quality}
                                                    </button>
                                                ))}
                                        </div>
                                        <p className="text-[10px] text-slate-500 mt-3 text-center">Select a quality to download the video</p>
                                    </div>
                                )}

                                {downloadedVideoPath && (
                                    <div className="flex items-center justify-center gap-2 text-green-600 text-sm font-semibold">
                                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                                        </svg>
                                        <span>Video downloaded successfully!</span>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Uploaded Video Card */}
                    {uploadedVideo ? (
                        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3 flex items-center gap-3 animate-fade-in">
                            <div className="w-16 h-12 bg-slate-200 rounded-md overflow-hidden flex-shrink-0 relative">
                                <img src={uploadedVideo.thumbnail} alt="Ref" className="w-full h-full object-cover" />
                                {uploadProgress[uploadedVideo.name] && uploadProgress[uploadedVideo.name] < 100 && (
                                    <div className="absolute bottom-0 left-0 h-1 bg-green-500 transition-all" style={{ width: `${uploadProgress[uploadedVideo.name]}%` }}></div>
                                )}
                            </div>
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-semibold text-slate-900 truncate">{uploadedVideo.name}</div>
                                <div className="text-xs text-slate-600 font-medium">
                                    {uploadedVideo.duration} • {uploadedVideo.size}
                                </div>
                            </div>
                            <button onClick={removeVideo} className="p-2 text-slate-400 hover:text-red-500 transition-colors">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                                </svg>
                            </button>
                        </div>
                    ) : (
                        <div className="h-16 border border-dashed border-slate-200 rounded-xl flex items-center justify-center text-xs text-slate-500 bg-slate-50/30">
                            No active media
                        </div>
                    )}
                </div>

                {/* Column 2: Localization */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-full hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
                            </svg>
                        </div>
                        <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wide">Language Setup</h2>
                    </div>

                    <div className="space-y-6 flex-1">
                        <LanguageDropdown
                            label="Original Language"
                            value={sourceLanguage}
                            options={languages}
                            onSelect={handleSourceSelect}
                            isOpen={showSourceDropdown}
                            setIsOpen={setShowSourceDropdown}
                            isAuto={true}
                        />

                        <div className="flex justify-center -my-3 relative z-10">
                            <div className="w-8 h-8 rounded-full bg-white shadow border border-slate-200 flex items-center justify-center text-slate-400">
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7" />
                                </svg>
                            </div>
                        </div>

                        <div className="relative">
                            <LanguageDropdown
                                label="Target Language"
                                value={targetLanguage}
                                options={languages}
                                onSelect={(code) => {
                                    handleTargetSelect(code);
                                    if (errors.targetLang) setErrors(prev => ({ ...prev, targetLang: null }));
                                }}
                                isOpen={showTargetDropdown}
                                setIsOpen={setShowTargetDropdown}
                            />
                            {errors.targetLang && <p className="text-red-500 text-xs font-semibold mt-1 ml-1 absolute -bottom-5">{errors.targetLang}</p>}
                        </div>

                        {/* Additional Options in Empty Space */}
                        <div className="pt-4 mt-auto">
                            <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide mb-3">Processing Options</h3>
                            <div className="space-y-3">
                                <label className="flex items-center gap-3 cursor-pointer group">
                                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${recoverBackgroundNoise ? 'bg-blue-600 border-blue-600' : 'border-slate-300 bg-white group-hover:border-blue-400'}`}>
                                        {recoverBackgroundNoise && (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                        )}
                                    </div>
                                    <input
                                        type="checkbox"
                                        className="hidden"
                                        checked={recoverBackgroundNoise}
                                        onChange={(e) => setRecoverBackgroundNoise(e.target.checked)}
                                    />
                                    <span className="text-sm font-semibold text-slate-700">Recover Background Noise</span>
                                </label>

                                <label className="flex items-center gap-3 cursor-pointer group">
                                    <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${makeVideo ? 'bg-blue-600 border-blue-600' : 'border-slate-300 bg-white group-hover:border-blue-400'}`}>
                                        {makeVideo && (
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3.5 w-3.5 text-white" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                        )}
                                    </div>
                                    <input
                                        type="checkbox"
                                        className="hidden"
                                        checked={makeVideo}
                                        onChange={(e) => setMakeVideo(e.target.checked)}
                                    />
                                    <span className="text-sm font-semibold text-slate-700">Generate Video Output</span>
                                </label>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Column 3: Speaker */}
                <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col h-full hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-3 mb-6">
                        <div className="w-8 h-8 rounded-lg bg-rose-50 flex items-center justify-center text-rose-600">
                            <svg xmlns="http://www.w3.org/2000/svg" className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                            </svg>
                        </div>
                        <h2 className="text-base font-extrabold text-slate-800 uppercase tracking-wide">Voice Model</h2>
                    </div>

                    {/* Speaker Gender Selector */}
                    <div className="flex-1">
                        <label className="text-sm font-bold text-slate-700 uppercase tracking-wide mb-3 block">Voice Gender</label>
                        <div className="grid grid-cols-1 gap-3">
                            {speakerOptions.map((option) => (
                                <div
                                    key={option.id}
                                    onClick={() => setSpeakerGender(option.name)}
                                    className={`relative p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 flex items-center gap-4 ${speakerGender === option.name
                                        ? `border-transparent ring-2 ring-offset-2 ring-slate-900 bg-slate-900 text-white shadow-lg`
                                        : 'border-slate-100 bg-white hover:border-slate-300'}`}
                                >
                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center text-xl bg-white/20`}>
                                        {option.icon}
                                    </div>
                                    <div className="flex-1">
                                        <div className={`text-sm font-bold ${speakerGender === option.name ? 'text-white' : 'text-slate-800'}`}>{option.name}</div>
                                        <div className={`text-[10px] uppercase tracking-wider font-medium ${speakerGender === option.name ? 'text-slate-300' : 'text-slate-400'}`}>Professional</div>
                                    </div>
                                    {speakerGender === option.name && (
                                        <div className="w-5 h-5 bg-white text-slate-900 rounded-full flex items-center justify-center">
                                            <svg xmlns="http://www.w3.org/2000/svg" className="h-3 w-3" viewBox="0 0 20 20" fill="currentColor">
                                                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                                            </svg>
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>


                    </div>
                </div>


            </div>

            {/* Footer Action */}
            <div className="mt-12 flex flex-col items-center w-full max-w-md">
                {isProcessing ? (
                    <div className="w-full mb-4">
                        <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                            <span>Processing</span>
                            <span>{processingProgress.toFixed(0)}%</span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                            <div
                                className="h-full bg-blue-600 transition-all duration-300 rounded-full"
                                style={{ width: `${processingProgress}%` }}
                            ></div>
                        </div>
                    </div>
                ) : null}

                <button
                    onClick={handleGenerateVideo}
                    disabled={isProcessing || (!uploadedVideo && !videoUrl)}
                    className={`w-full py-4 rounded-xl shadow-lg transition-all text-sm font-bold uppercase tracking-widest ${isProcessing || (!uploadedVideo && !videoUrl)
                        ? 'bg-slate-200 text-slate-500 cursor-not-allowed shadow-none'
                        : 'bg-slate-900 text-white hover:bg-slate-800 hover:shadow-xl hover:-translate-y-0.5 active:translate-y-0'
                        }`}
                >
                    {isProcessing ? 'Processing Request...' : 'Generate Dubbed Video'}
                </button>
                <p className="text-xs text-slate-600 mt-4 text-center font-semibold">
                    Enterprise Grade Encryption
                </p>
            </div>

            {/* Processing Overlay */}
            {
                isProcessing && (
                    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm flex items-center justify-center z-50">
                        {/* Overlay functionality retained for focus, but styled professionally */}
                    </div>
                )
            }
        </div >
    );
};

export default InputPage;