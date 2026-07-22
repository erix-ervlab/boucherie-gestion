import { useEffect, useState } from "react";
import {
  Alert,
  Card,
  Col,
  DatePicker,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import dayjs, { Dayjs } from "dayjs";

const { RangePicker } = DatePicker;

const fmtEur = (v: number | null | undefined) =>
  v == null ? "—" : `${Number(v).toLocaleString("fr-FR")} €`;
const fmtKg = (v: number | null | undefined) =>
  v == null ? "—" : `${Number(v).toLocaleString("fr-FR")} kg`;

export const RendementPage = () => {
  const [range, setRange] = useState<[Dayjs, Dayjs]>([
    dayjs().subtract(6, "month"),
    dayjs(),
  ]);
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams();
    if (range?.[0]) params.set("date_debut", range[0].format("YYYY-MM-DD"));
    if (range?.[1]) params.set("date_fin", range[1].format("YYYY-MM-DD"));
    setLoading(true);
    fetch(`/api/rendement/synthese?${params.toString()}`)
      .then((r) => r.json())
      .then(setData)
      .finally(() => setLoading(false));
  }, [range]);

  const m = data?.morceaux ?? {};
  const g = data?.global_magasin ?? {};
  const lignes = data?.lignes ?? [];

  return (
    <Space direction="vertical" style={{ width: "100%" }} size="large">
      <Space
        style={{ justifyContent: "space-between", width: "100%" }}
        wrap
      >
        <Typography.Title level={4} style={{ margin: 0 }}>
          Rendement de découpe — théorique vs réel
        </Typography.Title>
        <RangePicker
          value={range}
          onChange={(v) => v && setRange(v as [Dayjs, Dayjs])}
          allowClear={false}
          format="DD/MM/YYYY"
        />
      </Space>

      <Alert
        type="info"
        showIcon
        message="Vue indicative"
        description="Le théorique est dérivé des poids achetés × le rendement paramétré de chaque gamme ; le coût d'achat est réparti sur les PLU à la valeur marchande. Le « réel par PLU » ne voit que les ventes passées par un code PLU (le prix libre reste invisible). L'indicateur global en kg, lui, est fiable car le poids est saisi même en prix libre."
      />

      {/* Bilan matière des morceaux transformés */}
      <Card title="Morceaux transformés (théorique)" loading={loading}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic title="Entrée (acheté)" value={fmtKg(m.entree_kg)} />
          </Col>
          <Col span={6}>
            <Statistic
              title="Vendable théorique"
              value={fmtKg(m.vendable_theo_kg)}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Perte (os, gras, chutes)"
              value={`${fmtKg(m.perte_kg)}${
                m.taux_perte_pct != null ? ` (${m.taux_perte_pct} %)` : ""
              }`}
            />
          </Col>
          <Col span={6}>
            <Statistic title="Coût d'achat HT" value={fmtEur(m.cout_total_ht)} />
          </Col>
        </Row>
      </Card>

      {/* Indicateur global magasin, immunisé au prix libre */}
      <Card
        title="Bilan global magasin (kg — fiable, prix libre inclus)"
        loading={loading}
      >
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title="Acheté vendable (théo.)"
              value={fmtKg(g.kg_achetes_vendables)}
            />
          </Col>
          <Col span={6}>
            <Statistic title="Vendu (réel)" value={fmtKg(g.kg_vendus)} />
          </Col>
          <Col span={6}>
            <Statistic
              title="Écart"
              value={fmtKg(g.ecart_kg)}
              valueStyle={{ color: (g.ecart_kg ?? 0) < 0 ? "#cf1322" : undefined }}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title="Taux d'écoulement"
              value={g.taux_ecoulement_pct != null ? `${g.taux_ecoulement_pct} %` : "—"}
            />
          </Col>
        </Row>
        <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
          Sur une même période, ce que vous avez acheté (converti en kg
          vendables) face à ce que vous avez réellement vendu. Un écart marqué
          traduit du stock, de la casse/démarque, ou des rendements à ajuster —
          à lire comme une tendance, pas au kilo près.
        </Typography.Paragraph>
      </Card>

      {/* Détail par PLU */}
      <Card title="Par morceau / PLU produit" loading={loading}>
        <Table
          dataSource={lignes}
          rowKey="produit_id"
          size="small"
          pagination={false}
        >
          <Table.Column dataIndex="produit" title="PLU produit" />
          <Table.Column
            dataIndex="gammes"
            title="Issu de"
            render={(v: string[]) =>
              (v ?? []).map((n) => (
                <Tag key={n} color="geekblue">
                  {n}
                </Tag>
              ))
            }
          />
          <Table.Column
            dataIndex="theo_kg"
            title="Théo. produit"
            align="right"
            render={fmtKg}
            sorter={(a: any, b: any) => a.theo_kg - b.theo_kg}
          />
          <Table.Column
            dataIndex="vendu_kg"
            title="Vendu réel"
            align="right"
            render={fmtKg}
          />
          <Table.Column
            dataIndex="taux_ecoulement_pct"
            title="Écoulé"
            align="right"
            render={(v: number | null) =>
              v == null ? (
                "—"
              ) : (
                <Tag color={v > 110 ? "red" : v < 60 ? "orange" : "green"}>
                  {v} %
                </Tag>
              )
            }
          />
          <Table.Column
            dataIndex="cout_revient_kg"
            title="Coût revient /kg"
            align="right"
            render={fmtEur}
          />
          <Table.Column
            dataIndex="prix_vente"
            title="Prix vente /kg"
            align="right"
            render={fmtEur}
          />
          <Table.Column
            dataIndex="marge_pct"
            title="Marge"
            align="right"
            render={(v: number | null) =>
              v == null ? (
                "—"
              ) : (
                <Tag color={v < 0 ? "red" : v < 20 ? "orange" : "green"}>
                  {v} %
                </Tag>
              )
            }
          />
          <Table.Column
            dataIndex="ca_potentiel"
            title="CA potentiel"
            align="right"
            render={fmtEur}
          />
        </Table>
        {lignes.length === 0 && !loading && (
          <Alert
            style={{ marginTop: 12 }}
            type="warning"
            showIcon
            message="Aucun morceau transformé sur la période"
            description="Créez des gammes de découpe, puis reliez une référence d'achat à sa gamme dans « Correspondances » (colonne Gamme). Le théorique se calculera automatiquement à partir des poids achetés."
          />
        )}
      </Card>
    </Space>
  );
};
