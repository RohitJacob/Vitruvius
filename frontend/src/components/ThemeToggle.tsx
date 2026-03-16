import { useThemeStore } from "../stores/themeStore";

export default function ThemeToggle() {
  const { theme, toggle } = useThemeStore();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggle}
      className="relative w-10 h-5 rounded-full transition-colors duration-300 focus:outline-none"
      style={{ background: isDark ? "rgba(59,130,246,0.2)" : "rgba(59,130,246,0.12)" }}
      aria-label="Toggle theme"
    >
      <span
        className={`absolute top-0.5 w-4 h-4 rounded-full transition-all duration-300 flex items-center justify-center text-[9px] ${
          isDark
            ? "left-[22px] bg-brand-500 text-white"
            : "left-0.5 bg-brand-600 text-white"
        }`}
      >
        {isDark ? "☾" : "☀"}
      </span>
    </button>
  );
}
