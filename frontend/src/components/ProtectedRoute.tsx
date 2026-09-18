import { useEffect } from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import { fetchCurrentUser } from "@/store/slices/authSlice";
import type { UserRole } from "@/types";
import { ACCESS_TOKEN_KEY } from "@/api/client";

export default function ProtectedRoute({ allowedRoles }: { allowedRoles?: UserRole[] }) {
  const dispatch = useAppDispatch();
  const { user, status } = useAppSelector((s) => s.auth);
  const hasToken = Boolean(localStorage.getItem(ACCESS_TOKEN_KEY));

  useEffect(() => {
    if (hasToken && status === "idle") {
      dispatch(fetchCurrentUser());
    }
  }, [dispatch, hasToken, status]);

  if (!hasToken) return <Navigate to="/login" replace />;

  if (status === "loading" || status === "idle") {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-brand-200 border-t-brand-600" />
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
