import { useState, useEffect } from 'react';
import { 
  Globe, Search, History, Settings, FileText, Database, Play, 
  CheckCircle, AlertCircle, Server, RefreshCw, Sparkles,
  Zap, Brain, Download
} from 'lucide-react';
import { API_BASE_URL } from './config';
import {
  Button, Card, InputField, 
  EmptyState, FileListItem, FileContentItem
} from './components';

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
    } catch (error: unknown) {
      console.error('Scrape Error:', error);
      setStatus(`Network Error: ${error instanceof Error ? error.message : String(error)}`);
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
    } catch (error: unknown) {
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
    } catch (error: unknown) {
      console.error('Load File Error:', error);
      setSelectedFile({
        filename,
        content: { error: `Network Error loading file ${filename}: ${error instanceof Error ? error.message : String(error)}` }
      });
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <div className={`min-h-screen transition-all duration-500 animate-gradient-xy ${
      theme === 'dark' 
        ? 'bg-gradient-to-br from-gray-900 via-purple-900/80 to-violet-900/60' 
        : 'bg-gradient-to-br from-blue-50 via-indigo-50/80 to-purple-50/60'
    }`}>
      {/* Animated Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className={`absolute top-20 left-10 w-72 h-72 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float ${
          theme === 'dark' ? 'bg-purple-400' : 'bg-purple-300'
        }`} style={{ animationDelay: '0s' }}></div>
        <div className={`absolute top-40 right-20 w-72 h-72 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float ${
          theme === 'dark' ? 'bg-yellow-400' : 'bg-yellow-300'
        }`} style={{ animationDelay: '2s' }}></div>
        <div className={`absolute -bottom-8 left-20 w-72 h-72 rounded-full mix-blend-multiply filter blur-xl opacity-20 animate-float ${
          theme === 'dark' ? 'bg-pink-400' : 'bg-pink-300'
        }`} style={{ animationDelay: '4s' }}></div>
      </div>
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
                title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
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
              onClick={() => setActiveTab(id as 'scraper' | 'history' | 'settings')}
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
          <div className="space-y-8 animate-fade-in-up">
            {/* Hero Section */}
            <Card variant="glass" className="p-8 text-center">
              <div className="flex items-center justify-center mb-4">
                <div className="p-3 bg-gradient-primary rounded-2xl">
                  <Sparkles className="w-8 h-8 text-white animate-pulse" />
                </div>
              </div>
              <h2 className={`text-3xl font-bold mb-2 text-shadow ${
                theme === 'dark' ? 'text-white' : 'text-gray-900'
              }`}>AI-Powered Documentation Extraction</h2>
              <p className={`text-lg mb-6 ${
                theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
              }`}>Transform any documentation site into structured, searchable content</p>
              
              {/* Quick Stats */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    theme === 'dark' ? 'text-blue-400' : 'text-blue-600'
                  }`}>⚡</div>
                  <div className={`text-sm ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>Lightning Fast</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    theme === 'dark' ? 'text-green-400' : 'text-green-600'
                  }`}>🎯</div>
                  <div className={`text-sm ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>Precise Extraction</div>
                </div>
                <div className="text-center">
                  <div className={`text-2xl font-bold ${
                    theme === 'dark' ? 'text-purple-400' : 'text-purple-600'
                  }`}>🧠</div>
                  <div className={`text-sm ${
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>AI Enhanced</div>
                </div>
              </div>
            </Card>

            {/* Scraping Form */}
            <Card variant="glass" className="p-6">
              <div className="flex items-center mb-6">
                <div className="p-2 bg-gradient-success rounded-lg mr-3">
                  <Zap className="w-5 h-5 text-white" />
                </div>
                <h3 className={`text-xl font-semibold ${
                  theme === 'dark' ? 'text-white' : 'text-gray-900'
                }`}>Start New Extraction</h3>
              </div>
              
              <div className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <InputField
                    label="Documentation Website"
                    type="url"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                    placeholder="https://docs.example.com"
                    icon={Globe}
                    className="animate-slide-in-left"
                  />
                  <InputField
                    label="Topic/Section"
                    type="text"
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && scrapeUrl()}
                    placeholder="getting-started"
                    icon={Brain}
                    className="animate-slide-in-right"
                  />
                </div>

                <div className="flex justify-center">
                  <Button
                    onClick={scrapeUrl}
                    disabled={!baseUrl.trim() || !topic.trim() || isLoading || apiStatus !== 'online'}
                    loading={isLoading}
                    icon={isLoading ? undefined : Play}
                    size="lg"
                    className="shadow-glow hover:shadow-glow-hover"
                  >
                    {isLoading ? 'Extracting Documentation...' : 'Start Extraction'}
                  </Button>
                </div>
              </div>
            </Card>

            {/* Status Card */}
            <Card variant={statusType === 'error' ? 'default' : statusType === 'success' ? 'default' : 'glass'} className={`p-4 animate-scale-in ${
              statusType === 'error' ? 'border-red-500/50 bg-red-500/10' :
              statusType === 'success' ? 'border-green-500/50 bg-green-500/10' : ''
            }`}>
              <div className="flex items-start space-x-3">
                <div className="mt-0.5">
                  {statusType === 'error' && <AlertCircle className="w-5 h-5 text-red-500" />}
                  {statusType === 'success' && <CheckCircle className="w-5 h-5 text-green-500" />}
                  {statusType === 'normal' && <Brain className="w-5 h-5 text-blue-500" />}
                </div>
                <div className="flex-1">
                  <h4 className={`font-medium mb-1 ${
                    statusType === 'error' ? 'text-red-600 dark:text-red-400' :
                    statusType === 'success' ? 'text-green-600 dark:text-green-400' :
                    theme === 'dark' ? 'text-gray-200' : 'text-gray-800'
                  }`}>
                    {statusType === 'error' ? 'Extraction Error' :
                     statusType === 'success' ? 'Extraction Complete' :
                     'Status'}
                  </h4>
                  <p className={`text-sm whitespace-pre-wrap ${
                    statusType === 'error' ? 'text-red-500 dark:text-red-300' :
                    statusType === 'success' ? 'text-green-600 dark:text-green-400' :
                    theme === 'dark' ? 'text-gray-300' : 'text-gray-600'
                  }`}>
                    {status}
                  </p>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Files Tab */}
        {activeTab === 'history' && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in-up">
            {/* Available Files */}
            <Card variant="glass" className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="p-2 bg-gradient-secondary rounded-lg mr-3">
                    <Database className="w-5 h-5 text-white" />
                  </div>
                  <h2 className={`text-xl font-semibold ${
                    theme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>Documentation Library</h2>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={listScrapedFiles}
                  icon={RefreshCw}
                  className="shrink-0"
                >
                  Refresh
                </Button>
              </div>

              {scrapedFiles.length === 0 ? (
                <EmptyState
                  icon={FileText}
                  title="No documentation found"
                  description="Start by extracting some documentation content"
                  action={{
                    label: "Go to Scraper",
                    onClick: () => setActiveTab('scraper')
                  }}
                />
              ) : (
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {scrapedFiles.map((filename) => (
                    <FileListItem
                      key={filename}
                      filename={filename}
                      isSelected={selectedFile?.filename === filename}
                      onClick={() => loadFileContent(filename)}
                      icon={FileText}
                    />
                  ))}
                </div>
              )}
            </Card>

            {/* File Content */}
            <Card variant="glass" className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center">
                  <div className="p-2 bg-gradient-primary rounded-lg mr-3">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <h2 className={`text-xl font-semibold ${
                    theme === 'dark' ? 'text-white' : 'text-gray-900'
                  }`}>Content Viewer</h2>
                </div>
                {selectedFile && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={Download}
                    onClick={() => {
                      const dataStr = JSON.stringify(selectedFile.content, null, 2);
                      const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
                      const exportFileDefaultName = selectedFile.filename;
                      const linkElement = document.createElement('a');
                      linkElement.setAttribute('href', dataUri);
                      linkElement.setAttribute('download', exportFileDefaultName);
                      linkElement.click();
                    }}
                  >
                    Export
                  </Button>
                )}
              </div>

              {!selectedFile ? (
                <EmptyState
                  icon={Database}
                  title="Select a document"
                  description="Choose a file from the library to view its content"
                />
              ) : (
                <div className="space-y-4 max-h-96 overflow-y-auto">
                  {Object.entries(selectedFile.content).map(([url, content]) => (
                    <FileContentItem
                      key={url}
                      url={url}
                      content={typeof content === 'string' ? content : JSON.stringify(content, null, 2)}
                      theme={theme}
                      onCopyUrl={copyToClipboard}
                      onCopyContent={copyToClipboard}
                    />
                  ))}
                </div>
              )}
            </Card>
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
                      className={`px-4 py-2 rounded-lg transition-colors duration-300 ${
                        theme === 'dark'
                          ? 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30 active:scale-95'
                          : 'bg-blue-500/20 text-blue-600 hover:bg-blue-500/30 active:scale-95'
                      }`}
                      title={theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
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
