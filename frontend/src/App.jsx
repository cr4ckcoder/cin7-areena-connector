import React from 'react';
import ConfigurationForm from './components/ConfigurationForm';
import TestingTools from './components/TestingTools';
import Layout from './components/Layout';

function App() {
  return (
    <Layout>
      <ConfigurationForm />
      <TestingTools />
    </Layout>
  );
}

export default App;
