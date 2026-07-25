import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import TransitionOverlay from './components/TransitionOverlay';
import { TransitionProvider } from './components/TransitionContext';
import { CardModalProvider } from './components/CardModalContext';
import CardModal from './components/CardModal';
import GlobalCursor from './components/GlobalCursor';
import Home from './pages/Home';
import Explore from './pages/Explore';
import Browse from './pages/Browse';
import Culture from './pages/Culture';
import ArtifactDetail from './pages/ArtifactDetail';
import Identify from './pages/Identify';
import Login from './pages/Login';

function App() {
  return (
    <TransitionProvider>
      <CardModalProvider>
        <Navbar />
        <Routes>
          <Route path="/"         element={<Home />}           />
          <Route path="/explore"  element={<Explore />}        />
          <Route path="/browse"   element={<Browse />}         />
          <Route path="/culture"  element={<Culture />}        />
          <Route path="/artifact" element={<ArtifactDetail />} />
          <Route path="/identify" element={<Identify />}       />
          <Route path="/login"    element={<Login />}          />
        </Routes>
        <TransitionOverlay />
        {/* Card expand modal — Photography Page Transition */}
        <CardModal />
        {/* Global "Read" cursor — active over any .article-card */}
        <GlobalCursor />
      </CardModalProvider>
    </TransitionProvider>
  );
}

export default App;
