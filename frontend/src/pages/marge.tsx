import { useEffect, useMemo, useState } from "react";
import { Alert, Card, Col, DatePicker, Row, Statistic, Table, Tag, Typography, theme as antdTheme } from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import {
  Bar,
  BarChart,
  CartesianGrid,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const { RangePicker } = DatePicker;

const eur = (v: any) =>
  v == null
    ? "—"
    : `${Number(v).toLocaleString("fr-FR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })} €`;
const eur0 = (v: any) =>
  v == null ? "—" : `${Number(v).toLocaleString("fr-FR", { maximumFractionDigits: 0 })} €`;
const pct = (v: any) => (v == null ? "—" : `${v} %`);

export const MargePage = () => {
  const { token } = antdTheme.useToken();
  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [data, setData] = useState<any>(null);
  const [erreur, setErreur] = useState(false);

  useEffect(() => {
    fetch("/api/ventes/plage")
      .then((r) => r.json())
      .then((p) => p?.min && p?.max && setRange([dayjs(p.min), dayjs(p.max)]))
      .catch(() => {});
  }, []);

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    if (range?.[0]) p.set("date_debut", range[0].format("YYYY-MM-DD"));
    if (range?.[1]) p.set("date_fin", range[1].format("YYYY-MM-DD"));
    return p.toString();
  }, [range]);

  useEffect(() => {
    fetch(`/api/marge/par-famille?${qs}`)
      .then((r) => r.json())
      .then((d) => {
        setData(d);
        setErreur(false);
      })
      .catch(() => setErreur(true));
  }, [qs]);

  const lignes: any[] = data?.lignes ?? [];
  const total = data?.total;
  const peuAchats = data && (data.nb_achats_periode ?? 0) < 3;

  const couleurTaux = (r: any) => {
    if (!r.fiable) return token.colorTextDisabled;
    if (r.taux_marge == null || r.marge_cible == null) return token.colorText;
    const e = r.taux_marge - r.marge_cible;
    if (e >= 0) return token.colorSuccess;
    if (e >= -5) return token.colorWarning;
    return token.colorError;
  };

  const chartData = lignes
    .filter((r) => r.fiable && r.ca_ht > 0)
    .map((r) => ({ famille: r.famille, marge: r.marge_eur }));

  return (
    <div>
      <Row justify="space-between" align="middle" wrap style={{ marginBottom: 16, rowGap: 12 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Marge par famille
        </Typography.Title>
        <RangePicker
          value={range as any}
          format="DD/MM/YYYY"
          allowClear={false}
          onChange={(v) => v && setRange(v as [Dayjs, Dayjs])}
        />
      </Row>

      {erreur && <Alert type="warning" showIcon style={{ marginBottom: 16 }} message="Impossible de charger la marge." />}

      {peuAchats && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="Peu d'achats saisis sur cette période"
          description="La marge n'est représentative que si les achats couvrent bien la période de vente. Les familles sans achat sont grisées (marge non fiable). Saisissez plus de factures pour un calcul fiable."
        />
      )}

      {total && (
        <Row gutter={[16, 16]}>
          <Col xs={12} md={6}>
            <Card>
              <Statistic title="CA HT" value={eur(total.ca_ht)} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card>
              <Statistic title="Coût matière HT" value={eur(total.cout_ht)} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card>
              <Statistic title="Marge brute" value={eur(total.marge_eur)} />
            </Card>
          </Col>
          <Col xs={12} md={6}>
            <Card>
              <Statistic title="Taux de marge" value={pct(total.taux_marge)} />
            </Card>
          </Col>
        </Row>
      )}

      <Card title="Détail par famille" style={{ marginTop: 16 }}>
        <Table
          dataSource={lignes}
          rowKey="famille"
          size="small"
          pagination={false}
          columns={[
            {
              title: "Famille",
              dataIndex: "famille",
              render: (v: string, r: any) => (
                <span>
                  {v} {!r.fiable && r.ca_ht > 0 && <Tag>sans achat</Tag>}
                </span>
              ),
            },
            { title: "CA HT", dataIndex: "ca_ht", align: "right" as const, render: (v: any) => eur(v) },
            { title: "Coût HT", dataIndex: "cout_ht", align: "right" as const, render: (v: any) => eur(v) },
            { title: "Marge", dataIndex: "marge_eur", align: "right" as const, render: (v: any) => eur(v) },
            {
              title: "Taux",
              dataIndex: "taux_marge",
              align: "right" as const,
              render: (v: any, r: any) =>
                r.fiable ? (
                  <b style={{ color: couleurTaux(r) }}>{pct(v)}</b>
                ) : (
                  <span style={{ color: token.colorTextDisabled }}>—</span>
                ),
            },
            {
              title: "Cible",
              dataIndex: "marge_cible",
              align: "right" as const,
              render: (v: any) => (v != null ? `${v} %` : "—"),
            },
          ]}
          summary={() =>
            total ? (
              <Table.Summary.Row>
                <Table.Summary.Cell index={0}>
                  <b>TOTAL</b>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={1} align="right">
                  <b>{eur(total.ca_ht)}</b>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={2} align="right">
                  <b>{eur(total.cout_ht)}</b>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={3} align="right">
                  <b>{eur(total.marge_eur)}</b>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={4} align="right">
                  <b>{pct(total.taux_marge)}</b>
                </Table.Summary.Cell>
                <Table.Summary.Cell index={5} />
              </Table.Summary.Row>
            ) : null
          }
        />
      </Card>

      <Card title="Marge € par famille (familles avec achats)" style={{ marginTop: 16 }}>
        <div style={{ height: 320 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 60, bottom: 0, left: 8 }}>
              <CartesianGrid horizontal={false} stroke={token.colorSplit} />
              <XAxis
                type="number"
                tick={{ fill: token.colorTextSecondary, fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                tickFormatter={(v) => eur0(v)}
              />
              <YAxis
                type="category"
                dataKey="famille"
                width={120}
                tick={{ fill: token.colorTextSecondary, fontSize: 12 }}
                tickLine={false}
                axisLine={false}
              />
              <Tooltip
                contentStyle={{
                  background: token.colorBgElevated,
                  border: `1px solid ${token.colorBorderSecondary}`,
                  borderRadius: 8,
                  color: token.colorText,
                }}
                cursor={{ fill: token.colorSplit, opacity: 0.3 }}
                formatter={(v: any) => [eur(v), "Marge"]}
              />
              <Bar dataKey="marge" fill={token.colorPrimary} radius={[0, 4, 4, 0]} barSize={18}>
                <LabelList
                  dataKey="marge"
                  position="right"
                  formatter={(v: any) => eur0(v)}
                  style={{ fill: token.colorTextSecondary, fontSize: 11 }}
                />
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        {chartData.length === 0 && (
          <Typography.Text type="secondary">
            Aucune famille avec des achats sur la période — saisissez des factures pour voir les marges.
          </Typography.Text>
        )}
      </Card>
    </div>
  );
};
