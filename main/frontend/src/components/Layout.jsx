import { Link, useLocation } from 'react-router-dom';

function Layout({ children }) {
  const location = useLocation();
  
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <header className="bg-blue-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">Govt Document Intelligence System</h1>
            <nav className="flex gap-4">
              <Link
                to="/"
                className={`px-4 py-2 rounded transition ${
                  location.pathname === '/'
                    ? 'bg-blue-700'
                    : 'hover:bg-blue-500'
                }`}
              >
                Upload
              </Link>
              <Link
                to="/extractions"
                className={`px-4 py-2 rounded transition ${
                  location.pathname === '/extractions'
                    ? 'bg-blue-700'
                    : 'hover:bg-blue-500'
                }`}
              >
                Extractions
              </Link>
              <Link
                to="/chat"
                className={`px-4 py-2 rounded transition ${
                  location.pathname === '/chat'
                    ? 'bg-blue-700'
                    : 'hover:bg-blue-500'
                }`}
              >
                Chat
              </Link>
            </nav>
          </div>
        </div>
      </header>
      
      <main className="flex-1 container mx-auto px-4 py-8">
        {children}
      </main>
      
      <footer className="bg-gray-800 text-white py-4">
        <div className="container mx-auto px-4 text-center">
          <p>Govt Document Intelligence System v1.0.0</p>
        </div>
      </footer>
    </div>
  );
}

export default Layout;
