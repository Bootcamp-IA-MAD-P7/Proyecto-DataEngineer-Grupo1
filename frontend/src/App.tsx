import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { ApiStatusBadge } from "./components/ApiStatusBadge";
import DashboardPage from "./pages/DashboardPage";
import SearchPage from "./pages/SearchPage";
import PersonDetailPage from "./pages/PersonDetailPage";

function App() {
  return (
    <BrowserRouter>
      <nav
        aria-label="Main navigation"
        style={{
          display: "flex",
          alignItems: "center",
          gap: "1.5rem",
          padding: "0.8rem 1.2rem",
          borderBottom: "1px solid #ddd",
        }}
      >
        <Link to="/">Dashboard</Link>
        <Link to="/search">Search</Link>
        <span style={{ marginLeft: "auto" }}>
          <ApiStatusBadge />
        </span>
      </nav>
      <main style={{ padding: "1.2rem" }}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/person/:id" element={<PersonDetailPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
