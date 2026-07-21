import { useEffect, useState } from "react";
import { HistoryOutlined } from "@ant-design/icons";
import { Card, Segmented, Table, Tag, Typography } from "antd";
import dayjs from "dayjs";

const COULEUR: Record<string, string> = {
  création: "green",
  modification: "blue",
  suppression: "red",
  import: "geekblue",
};

export const HistoriquePage = () => {
  const [entite, setEntite] = useState<string>("");
  const [rows, setRows] = useState<any[]>([]);

  useEffect(() => {
    const qs = entite ? `?entite=${entite}` : "";
    fetch(`/api/journal${qs}`)
      .then((r) => r.json())
      .then((d) => setRows(Array.isArray(d) ? d : []))
      .catch(() => {});
  }, [entite]);

  return (
    <div>
      <Typography.Title level={3}>
        <HistoryOutlined /> Historique des opérations
      </Typography.Title>
      <Typography.Paragraph type="secondary">
        Trace persistante des créations, modifications et suppressions de factures,
        ainsi que des imports (ventes, catalogue). Conservée à travers les mises à jour.
      </Typography.Paragraph>

      <Segmented
        style={{ marginBottom: 16 }}
        value={entite}
        onChange={(v) => setEntite(v as string)}
        options={[
          { label: "Tout", value: "" },
          { label: "Achats", value: "achat" },
          { label: "Ventes", value: "ventes" },
          { label: "Catalogue", value: "catalogue" },
        ]}
      />

      <Card>
        <Table
          dataSource={rows}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 25, showSizeChanger: true }}
          columns={[
            {
              title: "Date / heure",
              dataIndex: "horodatage",
              width: 160,
              render: (v: string) => (v ? dayjs(v).format("DD/MM/YYYY HH:mm") : "—"),
            },
            {
              title: "Action",
              dataIndex: "action",
              width: 130,
              render: (v: string) => <Tag color={COULEUR[v] || "default"}>{v}</Tag>,
            },
            {
              title: "Type",
              dataIndex: "entite",
              width: 110,
              render: (v: string) => <Tag>{v}</Tag>,
            },
            { title: "Détail", dataIndex: "libelle" },
          ]}
        />
      </Card>
    </div>
  );
};
