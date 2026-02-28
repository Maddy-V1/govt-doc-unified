import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import UploadPage from './components/upload/UploadPage';
import ChatPage from './components/chat/ChatPage';
import ExtractionsPage from './pages/ExtractionsPage';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<UploadPage />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/extractions" element={<ExtractionsPage />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
