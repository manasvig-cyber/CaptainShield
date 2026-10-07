import { motion } from 'framer-motion';
import { ParallaxContainer } from './components/ParallaxContainer';
import { Dashboard } from './components/Dashboard';
import './styles/globals.css';

export function App() {
  return (
    <ParallaxContainer>
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{
          duration: 1.2,
          ease: [0.16, 1, 0.3, 1],
        }}
        style={{ width: '100%', height: '100%' }}
      >
        <Dashboard />
      </motion.div>
    </ParallaxContainer>
  );
}

export default App;
