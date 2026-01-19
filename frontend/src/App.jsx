import React from 'react';
import ConfigurationForm from './components/ConfigurationForm';
import TestingTools from './components/TestingTools';
import Layout from './components/Layout';
import OnDemandSync from './components/OnDemandSync';

function App() {
  return (
    <Layout>
      <ConfigurationForm />
      <TestingTools />
      <OnDemandSync />
    </Layout>
  );
}

export default App;
