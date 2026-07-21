import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { RefineThemes } from "@refinedev/antd";
import { ConfigProvider, theme as antdTheme } from "antd";
import frFR from "antd/locale/fr_FR";

// Palettes proposées (clé RefineThemes -> libellé FR).
export const PRESETS = [
  { key: "Red", label: "Rouge" },
  { key: "Blue", label: "Bleu" },
  { key: "Green", label: "Vert" },
  { key: "Purple", label: "Violet" },
  { key: "Orange", label: "Orange" },
  { key: "Magenta", label: "Magenta" },
  { key: "Yellow", label: "Jaune" },
] as const;

type Mode = "light" | "dark";

type ThemeCtx = {
  colorKey: string;
  mode: Mode;
  setColorKey: (k: string) => void;
  toggleMode: () => void;
};

const Ctx = createContext<ThemeCtx | null>(null);

export const useThemeMode = () => {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useThemeMode hors ThemeProvider");
  return ctx;
};

export const colorOf = (key: string): string =>
  (RefineThemes as any)[key]?.token?.colorPrimary ?? "#1677ff";

export const ThemeProvider = ({ children }: { children: ReactNode }) => {
  const [colorKey, setColorKey] = useState<string>(
    () => localStorage.getItem("theme.color") || "Red",
  );
  const [mode, setMode] = useState<Mode>(
    () => (localStorage.getItem("theme.mode") as Mode) || "light",
  );

  useEffect(() => localStorage.setItem("theme.color", colorKey), [colorKey]);
  useEffect(() => localStorage.setItem("theme.mode", mode), [mode]);

  const value = useMemo<ThemeCtx>(
    () => ({
      colorKey,
      mode,
      setColorKey,
      toggleMode: () => setMode((m) => (m === "light" ? "dark" : "light")),
    }),
    [colorKey, mode],
  );

  const base = (RefineThemes as any)[colorKey] ?? RefineThemes.Red;
  const theme = {
    ...base,
    algorithm:
      mode === "dark" ? antdTheme.darkAlgorithm : antdTheme.defaultAlgorithm,
  };

  return (
    <Ctx.Provider value={value}>
      <ConfigProvider theme={theme} locale={frFR}>
        {children}
      </ConfigProvider>
    </Ctx.Provider>
  );
};
