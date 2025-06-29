import { useState, useEffect } from 'react';
import { Globe, Search, Download, History, Settings, FileText, Link, Image, Database, Trash2, Play, CheckCircle, AlertCircle, Copy, ExternalLink, Server, RefreshCw } from 'lucide-react';
import { API_BASE_URL } from './config';

interface ScrapeResult {
  id: string;
  url: string;
  timestamp: Date;
  status: 'pending' | 'scraping' | 'completed' | 'error';
  data: {
    title?: string;
    description?: string;
    links?: string[];
    images?: string[];
    text?: string;
    metadata?: Record<string, any>;
  };
  error?: string;
}

interface ScrapedFile {
  filename: string;
  content: Record<string, string>;
}

function App() {
  const [baseUrl, setBaseUrl] = useState('');
  const [topic, setTopic] = useState('');
  const [status, setStatus] = useState('Scraping status will appear here.');
  const [statusType, setStatusType] = useState<'normal' | 'error' | 'success'>('normal');
  const [scrapedFiles, setScrapedFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<ScrapedFile | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'scraper' | 'history' | 'settings'>('scraper');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
    const interval = setInterval(checkApiHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load saved theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    }
    listScrapedFiles();
  }, []);

  // Theme toggle
  useEffect(() => {
    localStorage.setItem('theme', theme);
    document.documentElement.className = theme;
  }, [theme]);

  const checkApiHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`);
      if (response.ok) {
        setApiStatus('online');
      } else {
        setApiStatus('offline');
      }
    } catch (error) {
      setApiStatus('offline');
    }
  };

  const scrapeUrl = async () => {
    if (!baseUrl.trim() || !topic.trim()) {
      setStatus('Please enter both a website URL and a topic.');
      setStatusType('error');
      return;
    }

    if (apiStatus !== 'online') {
      setStatus('Backend API is offline. Please check the connection.');
      setStatusType('error');
      return;
    }

    setIsLoading(true);
    setStatus('Starting scrape...');
    setStatusType('normal');

    const fullUrl = `${baseUrl.replace(/\/+$/, '')}/${topic.replace(/^\/+|\/+$/g, '')}/`;
    console.log('Constructed URL:', fullUrl);

    try {
      const response = await fetch(`${API_BASE_URL}/api/scrape`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: fullUrl })
      });

      console.log('Scrape Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const text = await response.text();
        console.log('Scrape Response Body:', text.slice(0, 200));
        setStatus(`Error: HTTP ${response.status} - ${text.slice(0, 100) || response.statusText}`);
        setStatusType('error');
        return;
      }

      const result = await response.json();
      setStatus(`Success: ${result.message}. Pages found: ${result.pages_found}`);
      setStatusType('success');
      await listScrapedFiles();
    } catch (error: any) {
      console.error('Scrape Error:', error);
      setStatus(`Network Error: ${error.message}`);
      setStatusType('error');
    } finally {
      setIsLoading(false);
    }
  };

  const listScrapedFiles = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/list-scraped-data`);
      console.log('List Files Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const text = await response.text();
        console.log('List Files Response Body:', text.slice(0, 200));
        setScrapedFiles([]);
        return;
      }

      const result = await response.json();
      if (result.files && result.files.length > 0) {
        setScrapedFiles(result.files);
      } else {
        setScrapedFiles([]);
      }
    } catch (error: any) {
      console.error('List Files Error:', error);
      setScrapedFiles([]);
    }
  };

  const loadFileContent = async (filename: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/get-scraped-data/${filename}`);
      console.log('Load File Response Status:', response.status, response.statusText);

      if (!response.ok) {
        const text = await response.text();
        console.log('Load File Response Body:', text.slice(0, 200));
        setSelectedFile({
          filename,
          content: { error: `Error loading file ${filename}: HTTP ${response.status} - ${text.slice(0, 100) || response.statusText}` }
        });
        return;
      }

      const data = await response.json();
      if (typeof data === 'object' && data !== null) {
        setSelectedFile({
          filename,
          content: data
        });
      } else {
        setSelectedFile({
          filename,
          content: { data: JSON.stringify(data, null, 2) }
        });
      }
    } catch (error: any) {
      console.error('Load File Error:', error);
      setSelectedFile({
        filename,
        content: { error: `Network Error loading file ${filename}: ${error.message}` }
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className={`min-h-screen transition-all duration-300 ${
      theme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-purple-900 to-violet-900' 
        : 'bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50'
    }`}>
      {/* Header */}
      <header className={`backdrop-blur-md border-b transition-colors duration-300 ${
        theme === 'dark' 
          ? 'bg-black/20 border-white/10' 
          : 'bg-white/30 border-black/10'
      }`}>
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <Globe className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className={`text-2xl font-bold ${
                  theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>Talk Docs. Learn Fast. Powered by AI.</h1>
                <p className={`text-sm ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>Advanced Documentation Scraper</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* API Status Indicator */}
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-lg ${
                apiStatus === 'online' ? 'bg-green-500/20 text-green-500' :
                apiStatus === 'offline' ? 'bg-red-500/20 text-red-500' :
                'bg-yellow-500/20 text-yellow-500'
              }`}>
                <Server className="w-4 h-4" />
                <span className="text-sm font-medium">
                  {apiStatus === 'online' ? 'API Online' :
                   apiStatus === 'offline' ? 'API Offline' :
                   'Checking...'}
                </span>
              </div>
              
              <button
                onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                className={`p-2 rounded-lg transition-colors ${
                  theme === 'dark' 
                    ? 'bg-white/10 hover:bg-white/20 text-white' 
                    : 'bg-black/10 hover:bg-black/20 text-gray-900'
                }`}
              >
                {theme === 'dark' ? '☀️' : '🌙'}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* API Offline Warning */}
      {apiStatus === 'offline' && (
        <div className="bg-red-500/20 border-l-4 border-red-500 p-4 mx-6 mt-4 rounded-r-lg">
          <div className="flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
            <div>
              <p className={`font-medium ${theme === 'dark' ? 'text-red-400' : 'text-red-600'}`}>
                Backend API is offline
              </p>
              <p className={`text-sm ${theme === 'dark' ? 'text-red-300' : 'text-red-500'}`}>
                {import.meta.env.DEV 
                  ? 'Please start the backend server by running: npm run backend'
                  : 'Backend service is currently unavailable. Please try again later.'
                }
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav className="container mx-auto px-6 py-4">
        <div className={`flex space-x-1 p-1 rounded-xl backdrop-blur-md ${
          theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
        }`}>
          {[
            { id: 'scraper', label: 'Scraper', icon: Search },
            { id: 'history', label: 'Files', icon: History },
            { id: 'settings', label: 'Settings', icon: Settings }
          ].map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setActiveTab(id as any)}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-300 ${
                activeTab === id
                  ? theme === 'dark'
                    ? 'bg-white/20 text-white shadow-lg'
                    : 'bg-white/60 text-gray-900 shadow-lg'
                  : theme === 'dark'
                    ? 'text-gray-300 hover:bg-white/10'
                    : 'text-gray-600 hover:bg-white/30'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span className="font-medium">{label}</span>
            </button>
          ))}
        </div>
      </nav>

      <div className="container mx-auto px-6 pb-8">
        {/* Scraper Tab */}
        {activeTab === 'scraper' && (
          <div className="space-y-6">
            {/* Scrape New Content Section */}
            <div className={`p-6 rounded-2xl backdrop-blur-md ${
              theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
            }`}>
              <h2 className={`text-xl font-semibold mb-4 ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>Scrape New Content</h2>
              
              <div className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <input
                    type="text"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="Enter website URL (e.g., https://docs.agno.com/)"
                    className={`px-4 py-3 rounded-xl backdrop-blur-md transition-all duration-300 ${
                      theme === 'dark'
                        ? 'bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:bg-white/20 focus:border-blue-400'
                        : 'bg-white/60 border border-black/20 text-gray-900 placeholder-gray-500 focus:bg-white/80 focus:border-blue-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/50`}
                  />
                  <input
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && scrapeUrl()}
                    placeholder="Enter topic to learn (e.g., teams)"
                    className={`px-4 py-3 rounded-xl backdrop-blur-md transition-all duration-300 ${
                      theme === 'dark'
                        ? 'bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:bg-white/20 focus:border-blue-400'
                        : 'bg-white/60 border border-black/20 text-gray-900 placeholder-gray-500 focus:bg-white/80 focus:border-blue-500'
                    } focus:outline-none focus:ring-2 focus:ring-blue-500/50`}
                  />
                </div>

                <div className="flex justify-center">
                  <button
                    onClick={scrapeUrl}
                    disabled={!baseUrl.trim() || !topic.trim() || isLoading || apiStatus !== 'online'}
                    className="flex items-center space-x-2 px-8 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl hover:from-green-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium shadow-lg"
                  >
                    {isLoading ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        <span>Scraping...</span>
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        <span>Scrape</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Status Display */}
              <div className={`mt-4 p-4 rounded-xl border ${
                statusType === 'error' ? 'bg-red-500/20 border-red-500/30 text-red-500' :
                statusType === 'success' ? 'bg-green-500/20 border-green-500/30 text-green-500' :
                theme === 'dark' ? 'bg-white/10 border-white/20 text-gray-300' : 'bg-white/60 border-black/20 text-gray-700'
              } min-h-[50px] whitespace-pre-wrap`}>
                {status}
              </div>
            </div>
          </div>
        )}

        {/* Files Tab */}
        {activeTab === 'history' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Available Files */}
            <div className={`p-6 rounded-2xl backdrop-blur-md ${
              theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
            }`}>
              <div className="flex items-center justify-between mb-4">
                <h2 className={`text-xl font-semibold ${
                  theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>Available Docs Material</h2>
                <button
                  onClick={listScrapedFiles}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                    theme === 'dark'
                      ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
                      : 'bg-blue-500/20 text-blue-600 hover:bg-blue-500/30'
                  }`}
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Refresh</span>
                </button>
              </div>

              {scrapedFiles.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className={`w-16 h-16 mx-auto mb-4 ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`} />
                  <p className={`text-lg ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>No scraped files found</p>
                  <p className={`text-sm ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`}>Scrape some documentation to see files here</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {scrapedFiles.map((filename) => (
                    <div
                      key={filename}
                      onClick={() => loadFileContent(filename)}
                      className={`p-3 rounded-lg cursor-pointer transition-colors ${
                        selectedFile?.filename === filename
                          ? theme === 'dark' ? 'bg-blue-500/20 text-blue-400' : 'bg-blue-500/20 text-blue-600'
                          : theme === 'dark' ? 'bg-white/10 hover:bg-white/15 text-gray-200' : 'bg-white/60 hover:bg-white/80 text-gray-700'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        <FileText className="w-4 h-4" />
                        <span className="text-sm font-medium truncate">{filename}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* File Content */}
            <div className={`p-6 rounded-2xl backdrop-blur-md ${
              theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
            }`}>
              <h2 className={`text-xl font-semibold mb-4 ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>Documentation Content</h2>

              {!selectedFile ? (
                <div className="text-center py-12">
                  <Database className={`w-16 h-16 mx-auto mb-4 ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`} />
                  <p className={`text-lg ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>Select a file to view content</p>
                  <p className={`text-sm ${
                    theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                  }`}>Click on a file from the list to see its content</p>
                </div>
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {Object.entries(selectedFile.content).map(([url, content]) => (
                    <div
                      key={url}
                      className={`border-b pb-4 mb-4 ${
                        theme === 'dark' ? 'border-white/20' : 'border-black/20'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <h3 className={`font-medium text-sm ${
                          theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                        }`}>
                          Source URL: {url}
                        </h3>
                        <button
                          onClick={() => copyToClipboard(url)}
                          className={`p-1 rounded transition-colors ${
                            theme === 'dark'
                              ? 'hover:bg-white/10 text-gray-400'
                              : 'hover:bg-black/10 text-gray-600'
                          }`}
                        >
                          <Copy className="w-4 h-4" />
                        </button>
                      </div>
                      <pre className={`text-sm whitespace-pre-wrap break-words p-3 rounded-lg ${
                        theme === 'dark' ? 'bg-black/20 text-gray-300' : 'bg-white/60 text-gray-700'
                      }`}>
                        {content}
                      </pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className={`p-6 rounded-2xl backdrop-blur-md ${
            theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
          }`}>
            <h2 className={`text-xl font-semibold mb-6 ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>Settings</h2>

            <div className="space-y-6">
              <div>
                <h3 className={`text-lg font-medium mb-4 ${
                  theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                }`}>API Configuration</h3>
                <div className={`p-4 rounded-xl ${
                  theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                }`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`font-medium ${
                        theme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>Backend URL</p>
                      <p className={`text-sm ${
                        theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>{API_BASE_URL}</p>
                    </div>
                    <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                      apiStatus === 'online' ? 'bg-green-500/20 text-green-500' :
                      apiStatus === 'offline' ? 'bg-red-500/20 text-red-500' :
                      'bg-yellow-500/20 text-yellow-500'
                    }`}>
                      {apiStatus}
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className={`text-lg font-medium mb-4 ${
                  theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                }`}>Appearance</h3>
                <div className={`p-4 rounded-xl ${
                  theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                }`}>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className={`font-medium ${
                        theme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>Theme</p>
                      <p className={`text-sm ${
                        theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                      }`}>Choose your preferred theme</p>
                    </div>
                    <button
                      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                      className={`px-4 py-2 rounded-lg transition-colors ${
                        theme === 'dark'
                          ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
                          : 'bg-blue-500/20 text-blue-600 hover:bg-blue-500/30'
                      }`}
                    >
                      {theme === 'dark' ? '🌙 Dark' : '☀️ Light'}
                    </button>
                  </div>
                </div>
              </div>

              <div>
                <h3 className={`text-lg font-medium mb-4 ${
                  theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                }`}>About</h3>
                <div className={`p-4 rounded-xl ${
                  theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                }`}>
                  <p className={`text-sm ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    WebScraper Pro - Advanced documentation scraping tool with AI-powered content extraction.
                    Built with React, TypeScript, and FastAPI.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;