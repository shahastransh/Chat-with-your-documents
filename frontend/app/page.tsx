'use client';
import { useState } from 'react';

// Safely grab the URL and remove any trailing slashes to prevent 404 Not Found errors
const rawApiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
const BACKEND_URL = rawApiUrl.replace(/\/+$/, "");

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState('');
  const [sources, setSources] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');
  const [modelUsed, setModelUsed] = useState('');

  const handleUpload = async () => {
    if (!file) return alert('Please select a file first.');
    setLoading(true);
    setUploadStatus('Uploading and processing...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const res = await fetch(`${BACKEND_URL}/upload`, {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        setUploadStatus(`Success! Document chunked into ${data.chunks} parts.`);
      } else {
        setUploadStatus(`Error: ${data.detail}`);
      }
    } catch (err) {
      setUploadStatus('Failed to connect to the backend server.');
    }
    setLoading(false);
  };

  const handleChat = async () => {
    if (!query) return;
    setLoading(true);
    setResponse('');
    setSources([]);
    setModelUsed('');

    try {
      const res = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      const data = await res.json();
      
      if (res.ok) {
        setResponse(data.answer);
        setSources(data.sources || []);
        setModelUsed(data.model_used || '');
      } else {
        setResponse(`Error: ${data.detail}`);
      }
    } catch (err) {
      setResponse('Failed to connect to the backend server.');
    }
    setLoading(false);
  };

  return (
    <main className="max-w-4xl mx-auto p-8 font-sans text-gray-800">
      <h1 className="text-4xl font-bold mb-8 text-center text-blue-600">Chat With Your Document</h1>

      {/* Upload Section */}
      <div className="bg-white shadow-md p-6 rounded-xl border border-gray-100 mb-8">
        <h2 className="text-xl font-semibold mb-4">1. Upload Document (PDF / DOCX)</h2>
        <div className="flex flex-col sm:flex-row gap-4 items-center">
          <input 
            type="file" 
            accept=".pdf,.docx" 
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="border border-gray-300 p-2 rounded-lg bg-gray-50 w-full"
          />
          <button 
            onClick={handleUpload}
            disabled={loading}
            className="bg-blue-600 text-white px-8 py-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 font-medium transition-colors w-full sm:w-auto"
          >
            {loading ? 'Processing...' : 'Upload'}
          </button>
        </div>
        {uploadStatus && (
          <p className={`mt-4 text-sm font-medium ${uploadStatus.includes('Error') || uploadStatus.includes('Failed') ? 'text-red-500' : 'text-green-600'}`}>
            {uploadStatus}
          </p>
        )}
      </div>

      {/* Chat Section */}
      <div className="bg-white shadow-md p-6 rounded-xl border border-gray-100">
        <h2 className="text-xl font-semibold mb-4">2. Ask Questions</h2>
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., What is the main topic of this document?"
            className="border border-gray-300 p-3 rounded-lg w-full bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyDown={(e) => e.key === 'Enter' && handleChat()}
          />
          <button 
            onClick={handleChat}
            disabled={loading || !query}
            className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 disabled:bg-gray-400 font-medium transition-colors w-full sm:w-auto"
          >
            {loading ? 'Thinking...' : 'Ask AI'}
          </button>
        </div>
        
        {response && (
          <div className="bg-blue-50 p-5 rounded-lg border border-blue-100">
            <div className="flex justify-between items-center mb-3">
              <h3 className="font-bold text-blue-900">AI Answer:</h3>
              {modelUsed && <span className="text-xs bg-blue-200 text-blue-800 px-2 py-1 rounded-full">Model: {modelUsed}</span>}
            </div>
            <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">{response}</p>
            
            {sources.length > 0 && (
              <div className="mt-6 pt-4 border-t border-blue-200">
                <h4 className="text-sm font-bold text-gray-600 mb-2">Sources Retrieved:</h4>
                <ul className="list-disc pl-5 text-sm text-gray-600 space-y-2">
                  {sources.map((source, idx) => (
                    <li key={idx} className="line-clamp-2 italic">"{source}"</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  );
}