import { useThemeMode } from "../theme";

/**
 * Grafana intégré dans l'app via iframe (même origine, sous /grafana/).
 * Le thème suit celui de l'app. L'accès lecture est anonyme (rôle Viewer),
 * donc pas de second login pour consulter les tableaux.
 */
export const GrafanaPage = () => {
  const { mode } = useThemeMode();
  const src = `/grafana/?theme=${mode}`;
  return (
    <iframe
      src={src}
      title="Grafana — exploration"
      style={{
        width: "100%",
        height: "calc(100vh - 112px)",
        border: 0,
        borderRadius: 8,
      }}
    />
  );
};
