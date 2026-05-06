import { Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@/store/themeStore';
import { AnomalyProvider } from '@/store/anomalyStore';
import { Layout } from '@/components/layout/Layout';
import { Dashboard } from '@/pages/Dashboard';
import { AnomalyDetails } from '@/pages/AnomalyDetails';

export default function App() {
  return (
    <ThemeProvider>
      <AnomalyProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/details" element={<AnomalyDetails />} />
          </Routes>
        </Layout>
      </AnomalyProvider>
    </ThemeProvider>
  );
}
