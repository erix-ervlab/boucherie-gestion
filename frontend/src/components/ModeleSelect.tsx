import { useEffect, useState } from "react";
import { Select } from "antd";

/** Charge les modèles IA disponibles et mémorise le choix (localStorage,
 *  partagé entre le copilote et la lecture de factures). */
export function useModele() {
  const [modeles, setModeles] = useState<any[]>([]);
  const [modele, setModeleState] = useState<string>(
    () => localStorage.getItem("ia.modele") || "",
  );

  useEffect(() => {
    fetch("/api/modeles")
      .then((r) => r.json())
      .then((d) => {
        setModeles(d.modeles || []);
        setModeleState((cur) => cur || d.defaut || (d.modeles?.[0]?.id ?? ""));
      })
      .catch(() => {});
  }, []);

  const setModele = (v: string) => {
    setModeleState(v);
    localStorage.setItem("ia.modele", v);
  };

  return { modeles, modele, setModele };
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
