import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import FileUpload from './FileUpload';
import About from './About';
import Layout from './Layout';
import './App.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<FileUpload />} />
          <Route path="/about" element={<About />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;