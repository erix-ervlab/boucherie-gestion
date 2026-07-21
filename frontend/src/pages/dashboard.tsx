import { useEffect, useState } from "react";
import {
  EuroCircleOutlined,
  ShoppingOutlined,
  TagsOutlined,
} from "@ant-design/icons";
import { Card, Col, Row, Statistic, Table, Typography, Alert } from "antd";

type Stats = {
  ca_eur: number;
  kg: number;
  lignes: number;
  tickets: number;
  plu_distincts: number;
  lignes_annulees: number;
};

const euro = (v: number) =>
  (v ?? 0).toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

export const Dashboard = () => {
  const [stats, setStats] = useState<Stats | null>(null);
  const [vendeurs, setVendeurs] = useState<any[]>([]);
  const [jours, setJours] = useState<any[]>([]);
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    Promise.all([
      fetch("/api/ventes/stats").then((r) => r.json()),
      fetch("/api/ventes/par-vendeur").then((r) => r.json()),
      fetch("/api/ventes/par-jour").then((r) => r.json()),
    ])
      .then(([s, v, j]) => {
        setStats(s);
        setVendeurs(Array.isArray(v) ? v : []);
        setJours(Array.isArray(j) ? j : []);
      })
      .catch(() => setErreur(true));
  }, []);

  return (
    <div>
      <Typography.Title level={3}>Tableau de bord — ventes</Typography.Title>

      {erreur && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="Impossible de charger les statistiques."
        />
      )}

      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card>
            <Statistic
              title="Chiffre d'affaires"
              value={euro(stats?.ca_eur ?? 0)}
              prefix={<EuroCircleOutlined />}
              suffix="€"
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic
              title="Poids vendu"
              value={stats?.kg ?? 0}
              precision={1}
              suffix="kg"
              prefix={<ShoppingOutlined />}
            />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Tickets" value={stats?.tickets ?? 0} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic
              title="PLU vendus"
              value={stats?.plu_distincts ?? 0}
              prefix={<TagsOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card title="CA par jour">
            <Table
              dataSource={jours}
              rowKey="jour"
              size="small"
              pagination={false}
              columns={[
                { title: "Jour", dataIndex: "jour" },
                {
                  title: "CA (€)",
                  dataIndex: "ca_eur",
                  align: "right",
                  render: (v: number) => euro(v),
                },
                { title: "Lignes", dataIndex: "lignes", align: "right" },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title="CA par vendeur">
            <Table
              dataSource={vendeurs}
              rowKey="vendeur"
              size="small"
              pagination={false}
              columns={[
                { title: "Vendeur", dataIndex: "vendeur" },
                {
                  title: "CA (€)",
                  dataIndex: "ca_eur",
                  align: "right",
                  render: (v: number) => euro(v),
                },
                { title: "Lignes", dataIndex: "lignes", align: "right" },
              ]}
            />
          </Card>
        </Col>
      </Row>

      {stats && stats.lignes_annulees > 0 && (
        <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
          {stats.lignes_annulees} ligne(s) annulée(s) exclue(s) du CA · {stats.lignes} lignes comptées.
        </Typography.Paragraph>
      )}
    </div>
  );
};
