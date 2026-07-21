import { useEffect, useRef, useState } from "react";
import { InboxOutlined } from "@ant-design/icons";
import { useList } from "@refinedev/core";
import {
  Alert,
  Button,
  Card,
  DatePicker,
  Input,
  Progress,
  Select,
  Space,
  Spin,
  Switch,
  Table,
  Tag,
  Typography,
  Upload,
  message,
} from "antd";
import dayjs from "dayjs";

const euro = (v: any) =>
  v == null ? "—" : `${Number(v).toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;

export const AchatsPage = () => {
  const [draft, setDraft] = useState<any>(null);
  const [extracting, setExtracting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [saving, setSaving] = useState(false);
  const [achats, setAchats] = useState<any[]>([]);
  const timerRef = useRef<any>(null);

  const { data: famData } = useList({ resource: "familles", pagination: { mode: "off" } });
  const familles = famData?.data ?? [];
  const famOptions = familles.map((f: any) => ({ label: f.nom, value: f.id }));

  const loadAchats = () =>
    fetch("/api/achats")
      .then((r) => r.json())
      .then((d) => setAchats(Array.isArray(d) ? d : []))
      .catch(() => {});

  useEffect(() => {
    loadAchats();
  }, []);

  const setLigne = (i: number, patch: any) =>
    setDraft((d: any) => ({
      ...d,
      lignes: d.lignes.map((l: any, idx: number) => (idx === i ? { ...l, ...patch } : l)),
    }));

  const uploadProps = {
    showUploadList: false,
    accept: ".pdf",
    multiple: false,
    customRequest: async (opt: any) => {
      setExtracting(true);
      setDraft(null);
      // Barre de progression indéterminée : progresse vers ~92 % en attendant.
      setProgress(6);
      timerRef.current = setInterval(() => {
        setProgress((p) => (p >= 92 ? p : p + Math.max(1, Math.round((92 - p) / 14))));
      }, 900);
      try {
        const fd = new FormData();
        fd.append("file", opt.file);
        const r = await fetch("/api/achats/extraire", { method: "POST", body: fd });
        if (!r.ok) {
          const e = await r.json().catch(() => ({}));
          throw new Error(e.detail || `HTTP ${r.status}`);
        }
        const data = await r.json();
        setDraft(data);
        opt.onSuccess?.({}, opt.file);
        message.success("Facture lue — vérifiez et corrigez avant d'enregistrer.");
      } catch (e: any) {
        message.error("Lecture IA : " + (e.message || "échec"));
        opt.onError?.(e);
      } finally {
        clearInterval(timerRef.current);
        setProgress(100);
        setExtracting(false);
        setTimeout(() => setProgress(0), 800);
      }
    },
  };

  const manquantes = draft
    ? draft.lignes.filter((l: any) => l.est_produit && l.famille_id == null).length
    : 0;

  const valider = async () => {
    setSaving(true);
    try {
      const body = {
        fournisseur_id: draft.fournisseur_id ?? null,
        fournisseur_nom: draft.fournisseur,
        numero_facture: draft.numero_facture,
        date_facture: draft.date_facture,
        montant_ht: draft.montant_ht,
        montant_tva: draft.montant_tva,
        montant_ttc: draft.montant_ttc,
        fichier_nom: draft.fichier_nom,
        lignes: draft.lignes.map((l: any) => ({
          reference_fournisseur: l.reference ?? l.reference_fournisseur ?? null,
          designation: l.designation,
          quantite: l.quantite,
          poids_kg: l.poids_kg,
          unite: l.unite,
          prix_unitaire: l.prix_unitaire,
          montant_ht: l.montant_ht,
          taux_tva: l.taux_tva,
          numero_lot: l.numero_lot,
          origine: l.origine,
          est_produit: l.est_produit,
          famille_id: l.est_produit ? l.famille_id ?? null : null,
          sous_famille_id: null,
        })),
      };
      const r = await fetch("/api/achats", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.detail || `HTTP ${r.status}`);
      }
      const data = await r.json();
      message.success(
        `Facture enregistrée : ${data.nb_lignes} lignes, ${data.correspondances_apprises} correspondance(s) apprise(s).`,
      );
      setDraft(null);
      loadAchats();
    } catch (e: any) {
      message.error("Enregistrement : " + (e.message || "échec"));
    } finally {
      setSaving(false);
    }
  };

  const rows = (draft?.lignes ?? []).map((l: any, i: number) => ({ ...l, _i: i }));

  return (
    <div>
      <Typography.Title level={3}>Achats — factures fournisseurs</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Upload.Dragger {...uploadProps} disabled={extracting}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">
            {extracting ? "Lecture de la facture par l'IA…" : "Glissez une facture PDF ici, ou cliquez"}
          </p>
          <p className="ant-upload-hint">
            L'IA lit la facture ; vous vérifiez et corrigez chaque ligne avant d'enregistrer.
          </p>
        </Upload.Dragger>
      </Card>

      {extracting && (
        <Card style={{ marginBottom: 16 }}>
          <Space direction="vertical" align="center" style={{ width: "100%" }} size="middle">
            <Spin size="large" />
            <Typography.Text strong>
              Lecture de la facture par l'IA… (environ 30 secondes)
            </Typography.Text>
            <Progress
              percent={progress}
              status="active"
              showInfo={false}
              style={{ maxWidth: 420, width: "100%" }}
            />
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              Extraction des lignes, montants, lots et origines…
            </Typography.Text>
          </Space>
        </Card>
      )}

      {draft && (
        <Card
          title="Brouillon à vérifier"
          style={{ marginBottom: 16 }}
          extra={
            <Button type="primary" loading={saving} onClick={valider}>
              Valider et enregistrer
            </Button>
          }
        >
          <Space wrap style={{ marginBottom: 12 }}>
            <Input
              addonBefore="Fournisseur"
              value={draft.fournisseur}
              onChange={(e) => setDraft({ ...draft, fournisseur: e.target.value })}
              style={{ width: 280 }}
            />
            <Input
              addonBefore="N° facture"
              value={draft.numero_facture}
              onChange={(e) => setDraft({ ...draft, numero_facture: e.target.value })}
              style={{ width: 220 }}
            />
            <DatePicker
              format="DD/MM/YYYY"
              value={draft.date_facture ? dayjs(draft.date_facture) : null}
              onChange={(d) => setDraft({ ...draft, date_facture: d ? d.format("YYYY-MM-DD") : null })}
            />
            <Tag>HT {euro(draft.montant_ht)}</Tag>
            <Tag>TVA {euro(draft.montant_tva)}</Tag>
            <Tag color="blue">TTC {euro(draft.montant_ttc)}</Tag>
          </Space>

          {manquantes > 0 && (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 12 }}
              message={`${manquantes} ligne(s) produit sans famille — affectez-les pour un suivi de marge complet (vous pouvez enregistrer quand même).`}
            />
          )}

          <Table
            dataSource={rows}
            rowKey="_i"
            size="small"
            pagination={false}
            expandable={{
              expandedRowRender: (r: any) => (
                <span style={{ fontSize: 12 }}>
                  {r.numero_lot ? `Lot ${r.numero_lot}` : "Pas de lot"}
                  {r.origine ? ` · ${r.origine}` : ""}
                </span>
              ),
              rowExpandable: (r: any) => !!(r.numero_lot || r.origine),
            }}
            columns={[
              { title: "Réf", dataIndex: "reference", width: 90 },
              {
                title: "Désignation",
                dataIndex: "designation",
                render: (v: string, r: any) => (
                  <span>
                    {v} {r.connu && <Tag color="green">connu</Tag>}
                  </span>
                ),
              },
              {
                title: "Qté / Poids",
                width: 110,
                render: (_: any, r: any) =>
                  r.poids_kg != null
                    ? `${r.poids_kg} kg`
                    : r.quantite != null
                      ? `${r.quantite} ${r.unite ?? ""}`
                      : "—",
              },
              {
                title: "Montant HT",
                dataIndex: "montant_ht",
                width: 110,
                align: "right" as const,
                render: (v: any) => euro(v),
              },
              {
                title: "TVA",
                dataIndex: "taux_tva",
                width: 70,
                align: "right" as const,
                render: (v: any) => (v != null ? `${v} %` : "—"),
              },
              {
                title: "Produit ?",
                width: 90,
                render: (_: any, r: any) => (
                  <Switch
                    checked={r.est_produit}
                    size="small"
                    onChange={(v) =>
                      setLigne(r._i, { est_produit: v, famille_id: v ? r.famille_id : null })
                    }
                  />
                ),
              },
              {
                title: "Famille",
                width: 200,
                render: (_: any, r: any) =>
                  r.est_produit ? (
                    <Select
                      value={r.famille_id ?? undefined}
                      onChange={(v) => setLigne(r._i, { famille_id: v ?? null })}
                      options={famOptions}
                      placeholder="— à affecter —"
                      allowClear
                      showSearch
                      optionFilterProp="label"
                      size="small"
                      style={{ width: 190 }}
                    />
                  ) : (
                    <Tag>frais / non-produit</Tag>
                  ),
              },
            ]}
          />
        </Card>
      )}

      <Card title="Factures enregistrées">
        <Table
          dataSource={achats}
          rowKey="id"
          size="small"
          columns={[
            { title: "Fournisseur", dataIndex: "fournisseur" },
            { title: "N° facture", dataIndex: "numero_facture" },
            {
              title: "Date",
              dataIndex: "date_facture",
              render: (d: string) => (d ? dayjs(d).format("DD/MM/YYYY") : "—"),
            },
            { title: "Lignes", dataIndex: "nb_lignes", align: "right" as const },
            {
              title: "HT",
              dataIndex: "montant_ht",
              align: "right" as const,
              render: (v: any) => euro(v),
            },
            {
              title: "TTC",
              dataIndex: "montant_ttc",
              align: "right" as const,
              render: (v: any) => euro(v),
            },
          ]}
        />
      </Card>
    </div>
  );
};
