import Login from "./components/authentication/Login";
import InputPage from "./components/InputPage/InputPage";
import LandingPage from "./components/LandingPage/LandingPage";
import PreviewPage from './components/PreviewPage/PreviewPage';
import Register from "./components/authentication/Register";
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import Navbar from "./components/LandingPage/sections/Navbar";

const Layout = () => {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={
          <>
            <LandingPage />
            <div className="fixed inset-0 z-50">
              <Login />
            </div>
          </>
        } />
        <Route path="/register" element={
          <>
            <LandingPage />
            <div className="fixed inset-0 z-50">
              <Register />
            </div>
          </>
        } />
        <Route path="/input" element={<InputPage />} />
        <Route path="/preview" element={<PreviewPage />} />
        {/* Catch-all route for better user experience */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
};

function App() {
  return (
    <Router>
      <Layout />
    </Router>
  )
}
export default App
