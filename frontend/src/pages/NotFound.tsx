import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 text-center">
      <h1 className="font-display text-6xl font-extrabold text-brand-600">404</h1>
      <p className="text-slate-500 dark:text-slate-400">This page doesn't exist.</p>
      <Link to="/" className="btn-primary">
        Go home
      </Link>
    </div>
  );
}
