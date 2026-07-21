import { useEffect, useState } from "react";
import { InboxOutlined } from "@ant-design/icons";
import { Alert, Card, Space, Table, Typography, Upload, message } from "antd";
import type { UploadProps } from "antd";

export const ImportsPage = () => {
  const [journal, setJournal] = useState<any[]>([]);
  const [dernier, setDernier] = useState<any>(null);

  const chargerJournal = () =>
    fetch("/api/imports")
      .then((r) => r.json())
      .then((d) => setJournal(Array.isArray(d) ? d : []))
      .catch(() => {});

  useEffect(() => {
    chargerJournal();
  }, []);

  const draggerProps = (url: string, label: string): UploadProps => ({
    name: "file",
    multiple: false,
    action: url,
    maxCount: 1,
    onChange(info) {
      const { status, response } = info.file;
      if (status === "done") {
        message.success(`${label} : import réussi`);
        setDernier(response);
        chargerJournal();
      } else if (status === "error") {
        message.error(
          response?.detail
            ? `${label} : ${response.detail}`
            : `${label} : échec de l'import`,
        );
        setDernier(response);
      }
    },
  });

  return (
    <div>
      <Typography.Title level={3}>Import caisse &amp; catalogue</Typography.Title>

      <Space direction="vertical" style={{ width: "100%" }} size="large">
        <Card title="Déposer un export de ventes (.csv GDPdU de la caisse)">
          <Upload.Dragger {...draggerProps("/api/imports/ventes", "Ventes")}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Glissez le fichier CSV ici, ou cliquez</p>
            <p className="ant-upload-hint">
              Idempotent : réimporter une période chevauchante ne crée aucun doublon.
            </p>
          </Upload.Dragger>
        </Card>

        <Card title="Charger le catalogue PLU (.xlsx)">
          <Upload.Dragger {...draggerProps("/api/imports/catalogue", "Catalogue")}>
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">Glissez l'Excel du catalogue ici, ou cliquez</p>
          </Upload.Dragger>
        </Card>

        {dernier && (
          <Alert
            type="info"
            message="Résultat du dernier import"
            description={
              <pre style={{ margin: 0 }}>{JSON.stringify(dernier, null, 2)}</pre>
            }
          />
        )}

        <Card title="Journal des imports">
          <Table
            dataSource={journal}
            rowKey="id"
            size="small"
            columns={[
              { title: "Fichier", dataIndex: "fichier_nom" },
              { title: "Ajoutées", dataIndex: "nb_lignes_ajoutees", align: "right" },
              { title: "Déjà connues", dataIndex: "nb_lignes_deja_connues", align: "right" },
              { title: "Ignorées", dataIndex: "nb_lignes_ignorees", align: "right" },
              { title: "Anomalies", dataIndex: "nb_anomalies", align: "right" },
              {
                title: "Rapports Z",
                render: (_: any, r: any) =>
                  r.z_min != null ? `${r.z_min}–${r.z_max}` : "—",
              },
            ]}
          />
        </Card>
      </Space>
    </div>
  );
};
