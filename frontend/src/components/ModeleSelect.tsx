import { useEffect, useState } from "react";
import { Select } from "antd";

/** Charge les modèles IA d'un usage donné ('facture' ou 'copilot') et mémorise
 *  le choix (localStorage propre à chaque usage). Le choix mémorisé est
 *  revalidé contre la liste autorisée (sinon on retombe sur le défaut). */
export function useModele(usage: string) {
  const [modeles, setModeles] = useState<any[]>([]);
  const [defaut, setDefaut] = useState<string>("");
  const key = `ia.modele.${usage}`;
  const [modele, setModeleState] = useState<string>(
    () => localStorage.getItem(key) || "",
  );

  useEffect(() => {
    fetch(`/api/modeles?usage=${encodeURIComponent(usage)}`)
      .then((r) => r.json())
      .then((d) => {
        const ids = (d.modeles || []).map((m: any) => m.id);
        setModeles(d.modeles || []);
        setDefaut(d.defaut || "");
        setModeleState((cur) =>
          cur && ids.includes(cur) ? cur : d.defaut || ids[0] || "",
        );
      })
      .catch(() => {});
  }, [usage]);

  const setModele = (v: string) => {
    setModeleState(v);
    localStorage.setItem(key, v);
  };

  return { modeles, modele, setModele, defaut };
}

export function ModeleSelect({
  modeles,
  modele,
  setModele,
  size,
}: {
  modeles: any[];
  modele: string;
  setModele: (v: string) => void;
  size?: "small" | "middle" | "large";
}) {
  return (
    <Select
      value={modele || undefined}
      onChange={setModele}
      size={size}
      style={{ width: 250 }}
      placeholder="Modèle IA"
      options={modeles.map((m: any) => ({
        value: m.id,
        label: `${m.nom} — ${m.cout}`,
      }))}
    />
  );
}
