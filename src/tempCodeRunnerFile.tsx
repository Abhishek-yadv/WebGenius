import { useState, useEffect } from 'react';
import { Globe, Search, Download, History, Settings, FileText, Link, Image, Database, Trash2, Play, CheckCircle, AlertCircle, Copy, ExternalLink, Server } from 'lucide-react';

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

interface ScrapeOptions {
  extractText: boolean;
  extractLinks: boolean;
  extractImages: boolean;
  extractMetadata: boolean;
  followRedirects: boolean;
  timeout: number;
}

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [url, setUrl] = useState('');
  const [urls, setUrls] = useState<string[]>([]);
  const [options, setOptions] = useState<ScrapeOptions>({
    extractText: true,
    extractLinks: true,
    extractImages: false,
    extractMetadata: true,
    followRedirects: true,
    timeout: 30000
  });
  const [results, setResults] = useState<ScrapeResult[]>([]);
  const [isScrapingActive, setIsScrapingActive] = useState(false);
  const [activeTab, setActiveTab] = useState<'scraper' | 'history' | 'settings'>('scraper');
  const [theme, setTheme] = useState<'light' | 'dark'>('dark');
  const [apiStatus, setApiStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // Check API health on mount
  useEffect(() => {
    checkApiHealth();
    const interval = setInterval(checkApiHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  // Load saved data on mount
  useEffect(() => {
    const savedResults = localStorage.getItem('scrapeResults');
    if (savedResults) {
      try {
        const parsed = JSON.parse(savedResults);
        setResults(parsed.map((r: any) => ({
          ...r,
          timestamp: new Date(r.timestamp)
        })));
      } catch (e) {
        console.error('Error loading saved results:', e);
      }
    }
    const savedTheme = localStorage.getItem('theme') as 'light' | 'dark';
    if (savedTheme) {
      setTheme(savedTheme);
    }
  }, []);

  // Save results to localStorage
  useEffect(() => {
    localStorage.setItem('scrapeResults', JSON.stringify(results));
  }, [results]);

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

  const addUrl = () => {
    if (url.trim() && !urls.includes(url.trim())) {
      setUrls([...urls, url.trim()]);
      setUrl('');
    }
  };

  const removeUrl = (index: number) => {
    setUrls(urls.filter((_, i) => i !== index));
  };

  const scrapeWebsite = async (targetUrl: string): Promise<ScrapeResult['data']> => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/scrape`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: targetUrl,
          options: options
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.status === 'success' && data.result) {
        return data.result.data;
      } else {
        throw new Error(data.message || 'Unknown error occurred');
      }
    } catch (error) {
      console.error('Scraping error:', error);
      throw error;
    }
  };

  const startScraping = async () => {
    if (urls.length === 0 || apiStatus !== 'online') return;
    
    setIsScrapingActive(true);
    
    for (const targetUrl of urls) {
      const result: ScrapeResult = {
        id: Math.random().toString(36).substr(2, 9),
        url: targetUrl,
        timestamp: new Date(),
        status: 'scraping',
        data: {}
      };
      
      setResults(prev => [result, ...prev]);
      
      try {
        const scrapedData = await scrapeWebsite(targetUrl);
        setResults(prev => 
          prev.map(r => 
            r.id === result.id 
              ? { ...r, status: 'completed', data: scrapedData }
              : r
          )
        );
      } catch (error) {
        setResults(prev => 
          prev.map(r => 
            r.id === result.id 
              ? { ...r, status: 'error', error: error instanceof Error ? error.message : 'Failed to scrape website' }
              : r
          )
        );
      }
    }
    
    setIsScrapingActive(false);
    setUrls([]);
  };

  const exportResults = (format: 'json' | 'csv') => {
    const completedResults = results.filter(r => r.status === 'completed');
    if (completedResults.length === 0) return;

    let data: string;
    let filename: string;
    let mimeType: string;

    if (format === 'json') {
      data = JSON.stringify(completedResults, null, 2);
      filename = 'scrape-results.json';
      mimeType = 'application/json';
    } else {
      const headers = ['URL', 'Title', 'Description', 'Links Count', 'Images Count', 'Timestamp'];
      const rows = completedResults.map(result => [
        result.url,
        result.data.title || '',
        result.data.description || '',
        result.data.links?.length || 0,
        result.data.images?.length || 0,
        result.timestamp.toISOString()
      ]);
      
      data = [headers, ...rows].map(row => row.map(cell => `"${cell}"`).join(',')).join('\n');
      filename = 'scrape-results.csv';
      mimeType = 'text/csv';
    }

    const blob = new Blob([data], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const clearHistory = () => {
    setResults([]);
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
                }`}>WebScraper Pro</h1>
                <p className={`text-sm ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>Advanced Data Extraction Tool</p>
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
                Please start the backend server by running: <code className="bg-black/20 px-2 py-1 rounded">npm run backend</code>
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
            { id: 'history', label: 'History', icon: History },
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
            {/* URL Input Section */}
            <div className={`p-6 rounded-2xl backdrop-blur-md ${
              theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
            }`}>
              <h2 className={`text-xl font-semibold mb-4 ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>Add URLs to Scrape</h2>
              
              <div className="flex space-x-3 mb-4">
                <input
                  type="url"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addUrl()}
                  placeholder="https://example.com"
                  className={`flex-1 px-4 py-3 rounded-xl backdrop-blur-md transition-all duration-300 ${
                    theme === 'dark'
                      ? 'bg-white/10 border border-white/20 text-white placeholder-gray-400 focus:bg-white/20 focus:border-blue-400'
                      : 'bg-white/60 border border-black/20 text-gray-900 placeholder-gray-500 focus:bg-white/80 focus:border-blue-500'
                  } focus:outline-none focus:ring-2 focus:ring-blue-500/50`}
                />
                <button
                  onClick={addUrl}
                  disabled={!url.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:from-blue-600 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium"
                >
                  Add URL
                </button>
              </div>

              {urls.length > 0 && (
                <div className="space-y-2">
                  <h3 className={`font-medium ${
                    theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                  }`}>URLs to Scrape ({urls.length})</h3>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {urls.map((url, index) => (
                      <div
                        key={index}
                        className={`flex items-center justify-between p-3 rounded-lg ${
                          theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                        }`}
                      >
                        <span className={`text-sm truncate ${
                          theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                        }`}>{url}</span>
                        <button
                          onClick={() => removeUrl(index)}
                          className={`p-1 rounded hover:bg-red-500/20 text-red-500 transition-colors`}
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex justify-center mt-6">
                <button
                  onClick={startScraping}
                  disabled={urls.length === 0 || isScrapingActive || apiStatus !== 'online'}
                  className="flex items-center space-x-2 px-8 py-3 bg-gradient-to-r from-green-500 to-blue-500 text-white rounded-xl hover:from-green-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300 font-medium shadow-lg"
                >
                  {isScrapingActive ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      <span>Scraping...</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      <span>Start Scraping</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Results Section */}
            {results.length > 0 && (
              <div className={`p-6 rounded-2xl backdrop-blur-md ${
                theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
              }`}>
                <div className="flex items-center justify-between mb-4">
                  <h2 className={`text-xl font-semibold ${
                    theme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>Recent Results</h2>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => exportResults('json')}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                        theme === 'dark'
                          ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
                          : 'bg-blue-500/20 text-blue-600 hover:bg-blue-500/30'
                      }`}
                    >
                      <Download className="w-4 h-4" />
                      <span>JSON</span>
                    </button>
                    <button
                      onClick={() => exportResults('csv')}
                      className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                        theme === 'dark'
                          ? 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                          : 'bg-green-500/20 text-green-600 hover:bg-green-500/30'
                      }`}
                    >
                      <Download className="w-4 h-4" />
                      <span>CSV</span>
                    </button>
                  </div>
                </div>

                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {results.slice(0, 5).map((result) => (
                    <div
                      key={result.id}
                      className={`p-4 rounded-xl transition-all duration-300 ${
                        theme === 'dark' ? 'bg-white/10 hover:bg-white/15' : 'bg-white/60 hover:bg-white/80'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-3">
                          <div className={`p-2 rounded-lg ${
                            result.status === 'completed' ? 'bg-green-500/20' :
                            result.status === 'error' ? 'bg-red-500/20' :
                            result.status === 'scraping' ? 'bg-blue-500/20' : 'bg-gray-500/20'
                          }`}>
                            {result.status === 'completed' && <CheckCircle className="w-4 h-4 text-green-500" />}
                            {result.status === 'error' && <AlertCircle className="w-4 h-4 text-red-500" />}
                            {result.status === 'scraping' && <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
                          </div>
                          <div>
                            <p className={`font-medium ${
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            }`}>{result.data.title || 'Untitled Page'}</p>
                            <p className={`text-sm ${
                              theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                            }`}>{result.url}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => copyToClipboard(result.url)}
                            className={`p-2 rounded-lg transition-colors ${
                              theme === 'dark'
                                ? 'hover:bg-white/10 text-gray-400'
                                : 'hover:bg-black/10 text-gray-600'
                            }`}
                          >
                            <Copy className="w-4 h-4" />
                          </button>
                          <a
                            href={result.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className={`p-2 rounded-lg transition-colors ${
                              theme === 'dark'
                                ? 'hover:bg-white/10 text-gray-400'
                                : 'hover:bg-black/10 text-gray-600'
                            }`}
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        </div>
                      </div>

                      {result.status === 'completed' && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                          <div className={`p-3 rounded-lg ${
                            theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                          }`}>
                            <div className="flex items-center space-x-2 mb-2">
                              <Link className="w-4 h-4 text-blue-500" />
                              <span className={`text-sm font-medium ${
                                theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                              }`}>Links</span>
                            </div>
                            <p className={`text-lg font-bold ${
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            }`}>{result.data.links?.length || 0}</p>
                          </div>
                          <div className={`p-3 rounded-lg ${
                            theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                          }`}>
                            <div className="flex items-center space-x-2 mb-2">
                              <Image className="w-4 h-4 text-purple-500" />
                              <span className={`text-sm font-medium ${
                                theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                              }`}>Images</span>
                            </div>
                            <p className={`text-lg font-bold ${
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            }`}>{result.data.images?.length || 0}</p>
                          </div>
                          <div className={`p-3 rounded-lg ${
                            theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                          }`}>
                            <div className="flex items-center space-x-2 mb-2">
                              <FileText className="w-4 h-4 text-green-500" />
                              <span className={`text-sm font-medium ${
                                theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                              }`}>Text</span>
                            </div>
                            <p className={`text-lg font-bold ${
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            }`}>{result.data.text ? Math.floor(result.data.text.length / 100) : 0}k</p>
                          </div>
                          <div className={`p-3 rounded-lg ${
                            theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                          }`}>
                            <div className="flex items-center space-x-2 mb-2">
                              <Database className="w-4 h-4 text-orange-500" />
                              <span className={`text-sm font-medium ${
                                theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                              }`}>Metadata</span>
                            </div>
                            <p className={`text-lg font-bold ${
                              theme === 'dark' ? 'text-white' : 'text-gray-900'
                            }`}>{Object.keys(result.data.metadata || {}).length}</p>
                          </div>
                        </div>
                      )}

                      {result.status === 'error' && (
                        <p className="text-red-500 text-sm mt-2">{result.error}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
          <div className={`p-6 rounded-2xl backdrop-blur-md ${
            theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
          }`}>
            <div className="flex items-center justify-between mb-6">
              <h2 className={`text-xl font-semibold ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>Scraping History ({results.length})</h2>
              <button
                onClick={clearHistory}
                className="flex items-center space-x-2 px-4 py-2 bg-red-500/20 text-red-500 rounded-lg hover:bg-red-500/30 transition-colors"
              >
                <Trash2 className="w-4 h-4" />
                <span>Clear All</span>
              </button>
            </div>

            {results.length === 0 ? (
              <div className="text-center py-12">
                <History className={`w-16 h-16 mx-auto mb-4 ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`} />
                <p className={`text-lg ${
                  theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                }`}>No scraping history yet</p>
                <p className={`text-sm ${
                  theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                }`}>Start scraping some URLs to see results here</p>
              </div>
            ) : (
              <div className="space-y-4">
                {results.map((result) => (
                  <div
                    key={result.id}
                    className={`p-4 rounded-xl ${
                      theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className={`font-medium ${
                          theme === 'dark' ? 'text-white' : 'text-gray-900'
                        }`}>{result.data.title || 'Untitled Page'}</p>
                        <p className={`text-sm ${
                          theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                        }`}>{result.url}</p>
                        <p className={`text-xs ${
                          theme === 'dark' ? 'text-gray-400' : 'text-gray-500'
                        }`}>{result.timestamp.toLocaleString()}</p>
                      </div>
                      <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                        result.status === 'completed' ? 'bg-green-500/20 text-green-500' :
                        result.status === 'error' ? 'bg-red-500/20 text-red-500' :
                        'bg-blue-500/20 text-blue-500'
                      }`}>
                        {result.status}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className={`p-6 rounded-2xl backdrop-blur-md ${
            theme === 'dark' ? 'bg-white/10' : 'bg-white/40'
          }`}>
            <h2 className={`text-xl font-semibold mb-6 ${
              theme === 'dark' ? 'text-white' : 'text-gray-900'
            }`}>Scraping Options</h2>

            <div className="space-y-6">
              <div>
                <h3 className={`text-lg font-medium mb-4 ${
                  theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                }`}>Data Extraction</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { key: 'extractText', label: 'Extract Text Content', icon: FileText },
                    { key: 'extractLinks', label: 'Extract Links', icon: Link },
                    { key: 'extractImages', label: 'Extract Images', icon: Image },
                    { key: 'extractMetadata', label: 'Extract Metadata', icon: Database }
                  ].map(({ key, label, icon: Icon }) => (
                    <label
                      key={key}
                      className={`flex items-center space-x-3 p-4 rounded-xl cursor-pointer ${
                        theme === 'dark' ? 'bg-white/10 hover:bg-white/15' : 'bg-white/60 hover:bg-white/80'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={options[key as keyof ScrapeOptions] as boolean}
                        onChange={(e) => setOptions({ ...options, [key]: e.target.checked })}
                        className="rounded text-blue-500"
                      />
                      <Icon className="w-5 h-5 text-blue-500" />
                      <span className={`font-medium ${
                        theme === 'dark' ? 'text-white' : 'text-gray-900'
                      }`}>{label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className={`text-lg font-medium mb-4 ${
                  theme === 'dark' ? 'text-gray-200' : 'text-gray-700'
                }`}>Advanced Options</h3>
                <div className="space-y-4">
                  <label className={`flex items-center justify-between p-4 rounded-xl ${
                    theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                  }`}>
                    <span className={`font-medium ${
                      theme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>Follow Redirects</span>
                    <input
                      type="checkbox"
                      checked={options.followRedirects}
                      onChange={(e) => setOptions({ ...options, followRedirects: e.target.checked })}
                      className="rounded text-blue-500"
                    />
                  </label>
                  
                  <div className={`p-4 rounded-xl ${
                    theme === 'dark' ? 'bg-white/10' : 'bg-white/60'
                  }`}>
                    <label className={`block font-medium mb-2 ${
                      theme === 'dark' ? 'text-white' : 'text-gray-900'
                    }`}>
                      Timeout (seconds): {options.timeout / 1000}
                    </label>
                    <input
                      type="range"
                      min="5000"
                      max="60000"
                      step="5000"
                      value={options.timeout}
                      onChange={(e) => setOptions({ ...options, timeout: parseInt(e.target.value) })}
                      className="w-full"
                    />
                  </div>
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