import logo from './logo.svg';
import './App.css';
import FlightTable from './components/FlightTable';

function App() {
  return (
    <div style={{ padding: 20 }}>
      <h1>Flight Dashboard</h1>
      <FlightTable />
    </div>
  );
}

export default App;
