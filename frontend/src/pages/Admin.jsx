import { useState } from 'react';
import {
    Lock, User, Upload, FileText,
    CheckCircle, XCircle, LogOut,
    Database, Loader, Shield
} from 'lucide-react';
import { adminLogin, uploadDocument, getDocuments } from '../services/api';


// ─────────────────────────────────────────
// SUPPORTED LANGUAGES + FRAMEWORKS
// For the document upload form dropdowns
// Must match backend enums exactly
// ─────────────────────────────────────────

const LANGUAGES = [
    { value: 'python',     label: 'Python'     },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java',       label: 'Java'       },
];

const FRAMEWORKS = [
    { value: 'unknown',  label: 'General / Unknown' },
    { value: 'django',   label: 'Django'            },
    { value: 'flask',    label: 'Flask'             },
    { value: 'fastapi',  label: 'FastAPI'           },
    { value: 'express',  label: 'Express'           },
    { value: 'react',    label: 'React'             },
    { value: 'spring',   label: 'Spring'            },
];


// ─────────────────────────────────────────
// LOGIN FORM COMPONENT
// Shown when admin is not logged in
// ─────────────────────────────────────────

function LoginForm({ onLoginSuccess }) {

    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError]         = useState(null);


    const handleLogin = async () => {
        if (!username.trim() || !password.trim()) {
            setError('Please enter both username and password');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            const response = await adminLogin(username, password);
            onLoginSuccess(response.access_token);
        } catch (err) {
            const message =
                err.response?.data?.detail ||
                'Invalid credentials. Please try again.';
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };


    return (
        <div className="min-h-screen bg-white flex items-center justify-center p-8">
            <div className="w-full max-w-md">

                {/* ── Header ───────────────────── */}
                <div className="text-center mb-10">
                    <div className="inline-flex p-4 bg-red-50 rounded-3xl mb-4">
                        <Shield size={32} className="text-[#FF4B4B]" />
                    </div>
                    <h1 className="text-3xl font-black text-slate-900 italic tracking-tight">
                        ACMP Admin
                    </h1>
                    <p className="text-slate-400 text-sm font-black uppercase tracking-widest mt-2">
                        Knowledge Base Management
                    </p>
                </div>

                {/* ── Login Card ───────────────── */}
                <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-xl">

                    {/* Username */}
                    <div className="mb-5">
                        <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">
                            <User size={11} />
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                            placeholder="Enter admin username"
                            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-[#FF4B4B] transition-all"
                        />
                    </div>

                    {/* Password */}
                    <div className="mb-6">
                        <label className="flex items-center gap-2 text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">
                            <Lock size={11} />
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleLogin()}
                            placeholder="Enter admin password"
                            className="w-full bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 placeholder:text-slate-300 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-[#FF4B4B] transition-all"
                        />
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="flex items-center gap-2 bg-red-50 border border-red-100 rounded-xl px-4 py-3 mb-5">
                            <XCircle size={14} className="text-[#FF4B4B] shrink-0" />
                            <p className="text-xs font-medium text-red-500">{error}</p>
                        </div>
                    )}

                    {/* Login button */}
                    <button
                        onClick={handleLogin}
                        disabled={isLoading}
                        className="w-full bg-[#FF4B4B] hover:bg-[#e63939] text-white py-3 rounded-xl font-black text-xs uppercase tracking-widest shadow-md transition-all active:scale-95 disabled:opacity-50 flex items-center justify-center gap-2"
                    >
                        {isLoading
                            ? <Loader size={16} className="animate-spin" />
                            : <Lock size={16} />
                        }
                        {isLoading ? 'Signing In...' : 'Sign In'}
                    </button>

                </div>
            </div>
        </div>
    );
}


// ─────────────────────────────────────────
// DOCUMENTS TABLE COMPONENT
// Shows all uploaded documents
// ─────────────────────────────────────────

function DocumentsTable({ documents, isLoading }) {
    if (isLoading) {
        return (
            <div className="flex items-center justify-center py-12">
                <Loader size={20} className="animate-spin text-slate-300" />
            </div>
        );
    }

    if (!documents || documents.length === 0) {
        return (
            <div className="text-center py-12">
                <Database size={32} className="text-slate-200 mx-auto mb-3" />
                <p className="text-slate-400 text-sm font-black uppercase tracking-widest">
                    No documents yet
                </p>
                <p className="text-slate-300 text-xs mt-1">
                    Upload your first knowledge document above
                </p>
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-xl border border-slate-100">
            <table className="w-full">
                <thead>
                    <tr className="bg-slate-50 border-b border-slate-100">
                        <th className="text-left px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            Source
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            Language
                        </th>
                        <th className="text-left px-4 py-3 text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            Framework
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {documents.map((doc, index) => (
                        <tr
                            key={index}
                            className="border-b border-slate-50 hover:bg-slate-50 transition-colors"
                        >
                            <td className="px-4 py-3">
                                <div className="flex items-center gap-2">
                                    <FileText size={14} className="text-slate-300" />
                                    <span className="text-sm font-medium text-slate-600">
                                        {doc.source}
                                    </span>
                                </div>
                            </td>
                            <td className="px-4 py-3">
                                <span className="bg-red-50 text-[#FF4B4B] text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-lg">
                                    {doc.language}
                                </span>
                            </td>
                            <td className="px-4 py-3">
                                <span className="bg-slate-100 text-slate-500 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded-lg">
                                    {doc.framework}
                                </span>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}


// ─────────────────────────────────────────
// ADMIN DASHBOARD COMPONENT
// Shown after successful login
// Upload docs + view knowledge base
// ─────────────────────────────────────────

function AdminDashboard({ token, onLogout }) {

    const [file, setFile]             = useState(null);
    const [language, setLanguage]     = useState('python');
    const [framework, setFramework]   = useState('unknown');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadResult, setUploadResult] = useState(null);
    const [documents, setDocuments]   = useState([]);
    const [isLoadingDocs, setIsLoadingDocs] = useState(false);


    // ── Load documents on mount ───────────
    const loadDocuments = async () => {
        setIsLoadingDocs(true);
        try {
            const response = await getDocuments(token);
            setDocuments(response.documents || []);
        } catch {
            setDocuments([]);
        } finally {
            setIsLoadingDocs(false);
        }
    };

    // Load on first render
    useState(() => {
        loadDocuments();
    }, []);


    // ── File upload handler ───────────────
    const handleUpload = async () => {
        if (!file) return;

        setIsUploading(true);
        setUploadResult(null);

        try {
            const result = await uploadDocument(
                file, language, framework, token
            );
            setUploadResult({
                success: true,
                message: result.message,
                chunks:  result.chunks_stored
            });
            setFile(null);
            // Refresh documents list
            await loadDocuments();
        } catch (err) {
            const message =
                err.response?.data?.detail ||
                'Upload failed. Please try again.';
            setUploadResult({
                success: false,
                message
            });
        } finally {
            setIsUploading(false);
        }
    };


    return (
        <div className="max-w-[1280px] mx-auto p-8 font-sans bg-white min-h-screen">

            {/* ── Header ───────────────────────── */}
            <div className="flex items-center justify-between mb-12">
                <div>
                    <h1 className="text-4xl font-black text-slate-900 italic tracking-tight">
                        ACMP Admin
                    </h1>
                    <p className="text-slate-400 text-sm font-black uppercase tracking-[0.15em] mt-1">
                        Knowledge Base Management
                    </p>
                </div>

                <button
                    onClick={onLogout}
                    className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-600 px-5 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all active:scale-95"
                >
                    <LogOut size={14} />
                    Sign Out
                </button>
            </div>


            {/* ── Upload Section ───────────────── */}
            <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm mb-8">

                <div className="flex items-center gap-2 mb-6">
                    <Upload size={14} className="text-slate-400" />
                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                        Upload Knowledge Document
                    </p>
                </div>

                <div className="grid grid-cols-3 gap-6 mb-6">

                    {/* File picker */}
                    <div className="col-span-1">
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">
                            Document
                        </label>
                        <label className="flex items-center gap-3 bg-slate-50 border border-slate-200 rounded-xl px-4 py-3 cursor-pointer hover:border-[#FF4B4B] hover:bg-red-50 transition-all group">
                            <Upload
                                size={16}
                                className="text-slate-400 group-hover:text-[#FF4B4B] transition-colors shrink-0"
                            />
                            <span className="text-sm font-medium text-slate-500 truncate">
                                {file ? file.name : 'Choose file...'}
                            </span>
                            <input
                                type="file"
                                accept=".txt,.md,.pdf"
                                onChange={(e) => setFile(e.target.files[0])}
                                className="hidden"
                            />
                        </label>
                        <p className="text-[10px] text-slate-300 font-black uppercase tracking-widest mt-1">
                            .txt · .md · .pdf
                        </p>
                    </div>

                    {/* Language selector */}
                    <div>
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">
                            Language
                        </label>
                        <select
                            value={language}
                            onChange={(e) => setLanguage(e.target.value)}
                            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-[#FF4B4B] transition-all"
                        >
                            {LANGUAGES.map((lang) => (
                                <option key={lang.value} value={lang.value}>
                                    {lang.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Framework selector */}
                    <div>
                        <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2 block">
                            Framework
                        </label>
                        <select
                            value={framework}
                            onChange={(e) => setFramework(e.target.value)}
                            className="w-full bg-white border border-slate-200 rounded-xl px-4 py-3 text-sm font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-red-100 focus:border-[#FF4B4B] transition-all"
                        >
                            {FRAMEWORKS.map((fw) => (
                                <option key={fw.value} value={fw.value}>
                                    {fw.label}
                                </option>
                            ))}
                        </select>
                    </div>

                </div>

                {/* Upload result message */}
                {uploadResult && (
                    <div className={`
                        flex items-center gap-3 rounded-xl px-4 py-3 mb-5
                        ${uploadResult.success
                            ? 'bg-green-50 border border-green-100'
                            : 'bg-red-50 border border-red-100'
                        }
                    `}>
                        {uploadResult.success
                            ? <CheckCircle size={16} className="text-green-500 shrink-0" />
                            : <XCircle size={16} className="text-[#FF4B4B] shrink-0" />
                        }
                        <div>
                            <p className={`text-sm font-black ${uploadResult.success ? 'text-green-600' : 'text-red-500'}`}>
                                {uploadResult.message}
                            </p>
                            {uploadResult.success && uploadResult.chunks && (
                                <p className="text-[10px] font-black text-green-400 uppercase tracking-widest mt-0.5">
                                    {uploadResult.chunks} chunks stored in ChromaDB
                                </p>
                            )}
                        </div>
                    </div>
                )}

                {/* Upload button */}
                <button
                    onClick={handleUpload}
                    disabled={!file || isUploading}
                    className="flex items-center gap-2 bg-[#FF4B4B] hover:bg-[#e63939] text-white px-8 py-3 rounded-xl font-black text-xs uppercase tracking-widest shadow-md transition-all active:scale-95 disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    {isUploading
                        ? <Loader size={16} className="animate-spin" />
                        : <Upload size={16} />
                    }
                    {isUploading ? 'Uploading...' : 'Upload Document'}
                </button>

            </div>


            {/* ── Knowledge Base Section ───────── */}
            <div className="bg-white border border-slate-200 rounded-2xl p-8 shadow-sm">

                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <Database size={14} className="text-slate-400" />
                        <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                            Knowledge Base
                        </p>
                        {documents.length > 0 && (
                            <span className="bg-red-50 text-[#FF4B4B] text-[10px] font-black px-2 py-0.5 rounded-full">
                                {documents.length}
                            </span>
                        )}
                    </div>

                    {/* Refresh button */}
                    <button
                        onClick={loadDocuments}
                        disabled={isLoadingDocs}
                        className="flex items-center gap-1.5 text-slate-400 hover:text-slate-600 text-[10px] font-black uppercase tracking-widest transition-colors disabled:opacity-50"
                    >
                        <Loader
                            size={11}
                            className={isLoadingDocs ? 'animate-spin' : ''}
                        />
                        Refresh
                    </button>
                </div>

                <DocumentsTable
                    documents={documents}
                    isLoading={isLoadingDocs}
                />

            </div>

        </div>
    );
}


// ─────────────────────────────────────────
// ADMIN PAGE
// Entry point — manages login state
// Shows LoginForm or AdminDashboard
// Token stored in React state only
// Never in localStorage
// ─────────────────────────────────────────

export default function Admin() {

    const [token, setToken] = useState(null);

    const handleLoginSuccess = (accessToken) => {
        setToken(accessToken);
    };

    const handleLogout = () => {
        setToken(null);
    };

    // Show login if no token
    if (!token) {
        return <LoginForm onLoginSuccess={handleLoginSuccess} />;
    }

    // Show dashboard if logged in
    return (
        <AdminDashboard
            token={token}
            onLogout={handleLogout}
        />
    );
}