import { useRef } from 'react';
import { Upload, FileCode, X, Code } from 'lucide-react';
import usePipelineStore from '../../store/pipelineStore';


// ─────────────────────────────────────────
// SUPPORTED FILE TYPES
// ─────────────────────────────────────────

const SUPPORTED_EXTENSIONS = {
    py:   'python',
    js:   'javascript',
    jsx:  'javascript',
    ts:   'typescript',
    tsx:  'typescript',
    java: 'java',
};

const ACCEPT_STRING = '.py,.js,.jsx,.ts,.tsx';


// ─────────────────────────────────────────
// CODE INPUT COMPONENT
// Two modes — paste or file upload
// Switched via tabs at the top
// ─────────────────────────────────────────

export default function CodeInput() {

    const fileInputRef = useRef(null);

    const {
        originalCode,
        setOriginalCode,
        selectedFile,
        setSelectedFile,
        inputMode,
        setInputMode,
        setSelectedLanguage,
        pipelineStatus,
    } = usePipelineStore();

    const isRunning = pipelineStatus === 'running';


    // ─────────────────────────────────────────
    // FILE HANDLING
    // ─────────────────────────────────────────

    const handleFileSelect = (file) => {
        if (!file) return;

        // Auto detect language from extension
        const ext = file.name.split('.').pop()?.toLowerCase();
        const detectedLanguage = SUPPORTED_EXTENSIONS[ext];
        // console.log('detected lang:', detectedLanguage);
        if (detectedLanguage) {
            setSelectedLanguage(detectedLanguage);
        }
        else {
            return alert(`Unsupported file type .${ext}\nSupported types: ${Object.keys(SUPPORTED_EXTENSIONS).join(', ')}`);
        }

        // Read file content into store
        const reader = new FileReader();
        reader.onload = (e) => {
            setOriginalCode(e.target.result);
        };
        reader.readAsText(file);
        setSelectedFile(file);
    };


    const handleFileInputChange = (e) => {
        const file = e.target.files[0];
        if (file) handleFileSelect(file);
    };


    // Drag and drop handlers
    const handleDragOver = (e) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelect(file);
    };


    const handleClearFile = () => {
        setSelectedFile(null);
        setOriginalCode('');
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };


    // ─────────────────────────────────────────
    // RENDER
    // ─────────────────────────────────────────

    return (
        <div className="bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">

            {/* ── Tab Switcher ─────────────────── */}
            <div className="flex border-b border-slate-100">
                <button
                    onClick={() => setInputMode('paste')}
                    disabled={isRunning}
                    className={`flex items-center gap-2 px-6 py-4 text-xs font-black uppercase tracking-widest transition-all
                        ${inputMode === 'paste'
                            ? 'text-[#FF4B4B] border-b-2 border-[#FF4B4B] bg-red-50'
                            : 'text-slate-400 hover:text-slate-600'
                        }`}
                >
                    <Code size={14} />
                    Paste Code
                </button>

                <button
                    onClick={() => setInputMode('upload')}
                    disabled={isRunning}
                    className={`flex items-center gap-2 px-6 py-4 text-xs font-black uppercase tracking-widest transition-all
                        ${inputMode === 'upload'
                            ? 'text-[#FF4B4B] border-b-2 border-[#FF4B4B] bg-red-50'
                            : 'text-slate-400 hover:text-slate-600'
                        }`}
                >
                    <Upload size={14} />
                    Upload File
                </button>
            </div>


            {/* ── Paste Mode ───────────────────── */}
            {inputMode === 'paste' && (
                <div className="relative">
                    <textarea
                        value={originalCode}
                        onChange={(e) => setOriginalCode(e.target.value)}
                        disabled={isRunning}
                        placeholder={`Paste your legacy code here...\n\nSupported languages:\n• Python\n• JavaScript / TypeScript\n• Java`}
                        className="w-full h-72 p-6 font-mono text-sm text-slate-700 bg-slate-50 resize-none focus:outline-none focus:bg-white transition-colors placeholder:text-slate-300 disabled:opacity-50"
                        spellCheck={false}
                    />

                    {/* Character count */}
                    <div className="absolute bottom-3 right-4 text-[10px] font-black text-slate-300 uppercase tracking-widest">
                        {originalCode.length.toLocaleString()} chars
                    </div>
                </div>
            )}


            {/* ── Upload Mode ──────────────────── */}
            {inputMode === 'upload' && (
                <div className="p-6">

                    {/* File selected state */}
                    {selectedFile ? (
                        <div className="flex items-center justify-between bg-red-50 border border-red-100 rounded-xl px-5 py-4">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-white rounded-lg shadow-sm">
                                    <FileCode size={18} className="text-[#FF4B4B]" />
                                </div>
                                <div>
                                    <p className="text-sm font-black text-slate-700">
                                        {selectedFile.name}
                                    </p>
                                    <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                        {(selectedFile.size / 1024).toFixed(1)} KB
                                        {originalCode &&
                                            ` · ${originalCode.split('\n').length} lines`
                                        }
                                    </p>
                                </div>
                            </div>

                            {/* Clear file button */}
                            {!isRunning && (
                                <button
                                    onClick={handleClearFile}
                                    className="p-2 hover:bg-red-100 rounded-lg transition-colors"
                                >
                                    <X size={16} className="text-slate-400" />
                                </button>
                            )}
                        </div>

                    ) : (

                        /* Drag and drop zone */
                        <div
                            onDragOver={handleDragOver}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className="border-2 border-dashed border-slate-200 rounded-xl p-12 text-center cursor-pointer hover:border-[#FF4B4B] hover:bg-red-50 transition-all group"
                        >
                            <div className="flex flex-col items-center gap-3">
                                <div className="p-4 bg-slate-100 rounded-2xl group-hover:bg-red-100 transition-colors">
                                    <Upload
                                        size={24}
                                        className="text-slate-400 group-hover:text-[#FF4B4B] transition-colors"
                                    />
                                </div>
                                <div>
                                    <p className="text-sm font-black text-slate-600">
                                        Drop your file here
                                    </p>
                                    <p className="text-xs text-slate-400 mt-1">
                                        or click to browse
                                    </p>
                                </div>
                                <p className="text-[10px] font-black text-slate-300 uppercase tracking-widest">
                                    {ACCEPT_STRING}
                                </p>
                            </div>
                        </div>
                    )}

                    {/* Hidden file input */}
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={ACCEPT_STRING}
                        onChange={handleFileInputChange}
                        className="hidden"
                    />

                    {/* Code preview after file upload */}
                    {selectedFile && originalCode && (
                        <div className="mt-4 bg-slate-50 rounded-xl border border-slate-100 overflow-hidden">
                            <div className="px-4 py-2 border-b border-slate-100 flex items-center gap-2">
                                <p className="text-[10px] font-black text-slate-400 uppercase tracking-widest">
                                    Preview
                                </p>
                            </div>
                            <pre className="p-4 text-xs font-mono text-slate-600 overflow-auto max-h-48 whitespace-pre-wrap leading-relaxed">
                                {originalCode.slice(0, 1000)}
                                {originalCode.length > 1000 && (
                                    `\n\n... ${originalCode.length - 1000} more characters`
                                )}
                            </pre>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}





