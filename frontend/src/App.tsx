import { Routes, Route, Navigate } from "react-router-dom";
import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Register from "@/pages/Register";
import Dashboard from "@/pages/Dashboard";
import SymptomChecker from "@/pages/SymptomChecker";
import ImageDiagnosis from "@/pages/ImageDiagnosis";
import VoiceDiagnosis from "@/pages/VoiceDiagnosis";
import Chat from "@/pages/Chat";
import DiseaseLibrary from "@/pages/DiseaseLibrary";
import DiseaseDetail from "@/pages/DiseaseDetail";
import History from "@/pages/History";
import Profile from "@/pages/Profile";
import Family from "@/pages/Family";
import Appointments from "@/pages/Appointments";
import Messages from "@/pages/Messages";
import VideoCall from "@/pages/VideoCall";
import HealthTracking from "@/pages/HealthTracking";
import Coach from "@/pages/Coach";
import Emergency from "@/pages/Emergency";
import Settings from "@/pages/Settings";
import Admin from "@/pages/Admin";
import NotFound from "@/pages/NotFound";
import Layout from "@/components/Layout";
import ProtectedRoute from "@/components/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Video call — full screen, no sidebar */}
      <Route element={<ProtectedRoute />}>
        <Route path="/call/:roomId" element={<VideoCall />} />
      </Route>

      {/* Protected: all roles */}
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard"       element={<Dashboard />} />
          <Route path="/symptom-checker" element={<SymptomChecker />} />
          <Route path="/image-diagnosis" element={<ImageDiagnosis />} />
          <Route path="/voice-diagnosis" element={<VoiceDiagnosis />} />
          <Route path="/chat"            element={<Chat />} />
          <Route path="/diseases"        element={<DiseaseLibrary />} />
          <Route path="/diseases/:id"    element={<DiseaseDetail />} />
          <Route path="/history"         element={<History />} />
          <Route path="/profile"         element={<Profile />} />
          <Route path="/family"          element={<Family />} />
          <Route path="/appointments"    element={<Appointments />} />
          <Route path="/messages"        element={<Messages />} />
          <Route path="/health-tracking" element={<HealthTracking />} />
          <Route path="/coach"           element={<Coach />} />
          <Route path="/emergency"       element={<Emergency />} />
          <Route path="/settings"        element={<Settings />} />
        </Route>
      </Route>

      {/* Admin only */}
      <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
        <Route element={<Layout />}>
          <Route path="/admin" element={<Admin />} />
        </Route>
      </Route>

      {/* Redirect /home -> /dashboard for convenience */}
      <Route path="/home" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
