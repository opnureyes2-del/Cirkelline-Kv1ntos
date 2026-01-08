import { Link, useLocation } from "react-router-dom";
import {
  Activity,
  Settings,
  RefreshCw,
  Database,
  Cpu,
  Brain
} from "lucide-react";
import clsx from "clsx";

interface LayoutProps {
  children: React.ReactNode;
}

const navItems = [
  { path: "/", label: "Status", icon: Activity },
  { path: "/commander", label: "Commander", icon: Brain },
  { path: "/sync", label: "Sync", icon: RefreshCw },
  { path: "/models", label: "Modeller", icon: Database },
  { path: "/settings", label: "Indstillinger", icon: Settings },
];

export function Layout({ children }: LayoutProps) {
  const location = useLocation();

  return (
    <div className="flex flex-col h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-3 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          <Cpu className="w-6 h-6 text-cirkelline-500" />
          <span className="font-semibold text-gray-900 dark:text-white">
            Cirkelline Local Agent
          </span>
        </div>
        <div className="text-xs text-gray-500 dark:text-gray-400">
          v0.1.0
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 overflow-auto p-4">
        {children}
      </main>

      {/* Navigation */}
      <nav className="flex items-center justify-around py-2 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;

          return (
            <Link
              key={item.path}
              to={item.path}
              className={clsx(
                "flex flex-col items-center gap-1 px-3 py-1 rounded-lg transition-colors",
                isActive
                  ? "text-cirkelline-600 dark:text-cirkelline-400"
                  : "text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="text-xs">{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
