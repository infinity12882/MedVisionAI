import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard, Stethoscope, Camera, Mic, MessageCircle,
  BookOpen, History, ShieldCheck, Moon, Sun, LogOut, Menu, X,
  Activity, Users, Calendar, MessageSquare, Heart, MapPin, Dumbbell, Settings,
} from "lucide-react";
import clsx from "clsx";
import { useAppDispatch, useAppSelector } from "@/hooks/redux";
import { logout } from "@/store/slices/authSlice";
import { setLanguage, toggleDarkMode } from "@/store/slices/uiSlice";

const PATIENT_NAV = [
  { to: "/dashboard",       icon: LayoutDashboard, key: "nav.dashboard"       },
  { to: "/symptom-checker", icon: Stethoscope,     key: "nav.symptom_checker" },
  { to: "/image-diagnosis", icon: Camera,          key: "nav.image_diagnosis" },
  { to: "/voice-diagnosis", icon: Mic,             key: "nav.voice_diagnosis" },
  { to: "/chat",            icon: MessageCircle,   key: "nav.chat"            },
  { to: "/diseases",        icon: BookOpen,        key: "nav.diseases"        },
  { to: "/family",          icon: Users,           key: "nav.family"          },
  { to: "/appointments",    icon: Calendar,        key: "nav.appointments"    },
  { to: "/messages",        icon: MessageSquare,   key: "nav.messages"        },
  { to: "/health-tracking", icon: Heart,           key: "nav.health_tracking" },
  { to: "/coach",           icon: Dumbbell,        key: "nav.coach"           },
  { to: "/emergency",       icon: MapPin,          key: "nav.emergency"       },
  { to: "/history",         icon: History,         key: "nav.history"         },
  { to: "/settings",        icon: Settings,        key: "nav.settings"        },
];

const DOCTOR_NAV = [
  { to: "/dashboard",    icon: LayoutDashboard, key: "nav.dashboard"    },
  { to: "/appointments", icon: Calendar,        key: "nav.appointments" },
  { to: "/messages",     icon: MessageSquare,   key: "nav.messages"     },
  { to: "/diseases",     icon: BookOpen,        key: "nav.diseases"     },
  { to: "/history",      icon: History,         key: "nav.history"      },
  { to: "/settings",     icon: Settings,        key: "nav.settings"     },
];

const ADMIN_NAV = [
  { to: "/dashboard", icon: LayoutDashboard, key: "nav.dashboard" },
  { to: "/admin",     icon: ShieldCheck,     key: "nav.admin"     },
  { to: "/diseases",  icon: BookOpen,        key: "nav.diseases"  },
  { to: "/settings",  icon: Settings,        key: "nav.settings"  },
];

const LANGS = [
  { code: "en", label: "EN" },
  { code: "uz", label: "UZ" },
  { code: "ru", label: "RU" },
];

export default function Layout() {
  const { t, i18n } = useTranslation();
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { user } = useAppSelector((s) => s.auth);
  const { darkMode, language } = useAppSelector((s) => s.ui);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", darkMode);
  }, [darkMode]);

  function handleLangChange(lang: string) {
    dispatch(setLanguage(lang as "en" | "uz" | "ru"));
    i18n.changeLanguage(lang);
  }

  const navItems =
    user?.role === "admin"  ? ADMIN_NAV  :
    user?.role === "doctor" ? DOCTOR_NAV : PATIENT_NAV;

  function handleLogout() {
    dispatch(logout());
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-slate-950">
      {sidebarOpen && (
        <div className="fixed inset-0 z-30 bg-black/40 lg:hidden" onClick={() => setSidebarOpen(false)} />
      )}

      <aside className={clsx(
        "fixed inset-y-0 left-0 z-40 flex w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900 transition-transform lg:static lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex h-16 shrink-0 items-center gap-2 border-b border-slate-200 px-6 dark:border-slate-800">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">
            <Activity size={18} />
          </div>
          <span className="font-display text-lg font-bold text-slate-900 dark:text-white">{t("app_name")}</span>
        </div>

        <nav className="flex-1 overflow-y-auto p-3 space-y-0.5">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => clsx(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-900/30 dark:text-brand-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              )}
            >
              <item.icon size={17} />
              {t(item.key)}
            </NavLink>
          ))}
        </nav>

        <div className="shrink-0 border-t border-slate-200 p-4 dark:border-slate-800">
          <div className="mb-3 flex items-center gap-3 px-1">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-900/40 dark:text-brand-300">
              {user?.full_name?.[0]?.toUpperCase() ?? "U"}
            </div>
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">{user?.full_name}</p>
              <p className="truncate text-xs capitalize text-slate-500 dark:text-slate-400">{user?.role}</p>
            </div>
          </div>
          <button onClick={handleLogout} className="btn-ghost w-full justify-start text-red-600 dark:text-red-400">
            <LogOut size={16} />
            {t("nav.logout")}
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur-md dark:border-slate-800 dark:bg-slate-900/80 sm:px-6">
          <button className="lg:hidden" onClick={() => setSidebarOpen(true)}>
            <Menu size={22} />
          </button>
          <Link to="/dashboard" className="font-display text-base font-bold text-slate-900 dark:text-white lg:hidden">
            {t("app_name")}
          </Link>

          <div className="ml-auto flex items-center gap-2">
            <div className="flex overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
              {LANGS.map((l) => (
                <button
                  key={l.code}
                  onClick={() => handleLangChange(l.code)}
                  className={clsx(
                    "px-2.5 py-1.5 text-xs font-bold transition-colors",
                    language === l.code
                      ? "bg-brand-600 text-white"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  )}
                >
                  {l.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => dispatch(toggleDarkMode())}
              className="flex h-9 w-9 items-center justify-center rounded-lg text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 transition-colors"
            >
              {darkMode ? <Sun size={18} /> : <Moon size={18} />}
            </button>
          </div>
        </header>

        <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>

      {sidebarOpen && (
        <button
          className="fixed right-4 top-4 z-50 flex h-9 w-9 items-center justify-center rounded-full bg-white shadow-lg lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <X size={18} />
        </button>
      )}
    </div>
  );
}
