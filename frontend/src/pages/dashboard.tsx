import { useEffect, useMemo, useState } from "react";
import {
  EuroCircleOutlined,
  ShoppingCartOutlined,
  ShoppingOutlined,
  TagsOutlined,
} from "@ant-design/icons";
import {
  Alert,
  Card,
  Col,
  DatePicker,
  Row,
  Select,
  Space,
  Statistic,
  Typography,
  theme as antdTheme,
} from "antd";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const { RangePicker } = DatePicker;

const eur0 = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  maximumFractionDigits: 0,
});
const eur2 = new Intl.NumberFormat("fr-FR", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const useChartTheme = () => {
  const { token } = antdTheme.useToken();
  return {
    primary: token.colorPrimary,
    text: token.colorTextSecondary,
    grid: token.colorSplit,
    surface: token.colorBgElevated,
    border: token.colorBorderSecondary,
    ink: token.colorText,
  };
};

export const Dashboard = () => {
  const t = useChartTheme();

  const [range, setRange] = useState<[Dayjs, Dayjs] | null>(null);
  const [famille, setFamille] = useState<number | undefined>(undefined);
  const [familles, setFamilles] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [serie, setSerie] = useState<any[]>([]);
  const [parFamille, setParFamille] = useState<any[]>([]);
  const [parHeure, setParHeure] = useState<any[]>([]);
  const [parVendeur, setParVendeur] = useState<any[]>([]);
  const [top, setTop] = useState<any[]>([]);
  const [erreur, setErreur] = useState(false);

  // Familles (pour le filtre) + plage de dates par défaut.
  useEffect(() => {
    fetch("/api/familles?_end=100&_sort=nom&_order=ASC")
      .then((r) => r.json())
      .then((d) => setFamilles(Array.isArray(d) ? d : []))
      .catch(() => {});
    fetch("/api/ventes/plage")
      .then((r) => r.json())
      .then((p) => {
        if (p?.min && p?.max) setRange([dayjs(p.min), dayjs(p.max)]);
      })
      .catch(() => {});
  }, []);

  const qs = useMemo(() => {
    const p = new URLSearchParams();
    if (range?.[0]) p.set("date_debut", range[0].format("YYYY-MM-DD"));
    if (range?.[1]) p.set("date_fin", range[1].format("YYYY-MM-DD"));
    return p;
  }, [range]);

  useEffect(() => {
    const p = new URLSearchParams(qs);
    if (famille != null) p.set("famille_id", String(famille));
    const s = p.toString();
    const sansFamille = qs.toString(); // par-famille = la ventilation elle-même

    Promise.all([
      fetch(`/api/ventes/stats?${s}`).then((r) => r.json()),
      fetch(`/api/ventes/par-jour?${s}`).then((r) => r.json()),
      fetch(`/api/ventes/par-famille?${sansFamille}`).then((r) => r.json()),
      fetch(`/api/ventes/par-heure?${s}`).then((r) => r.json()),
      fetch(`/api/ventes/par-vendeur?${s}`).then((r) => r.json()),
      fetch(`/api/ventes/top-produits?${s}`).then((r) => r.json()),
    ])
      .then(([st, sj, pf, ph, pv, tp]) => {
        setStats(st);
        setSerie(Array.isArray(sj) ? sj : []);
        setParFamille(Array.isArray(pf) ? pf : []);
        setParHeure(Array.isArray(ph) ? ph : []);
        setParVendeur(Array.isArray(pv) ? pv : []);
        setTop(Array.isArray(tp) ? tp : []);
        setErreur(false);
      })
      .catch(() => setErreur(true));
  }, [qs, famille]);

  const tooltipStyle = {
    background: t.surface,
    border: `1px solid ${t.border}`,
    borderRadius: 8,
    color: t.ink,
  };
  const axis = { stroke: t.text, fontSize: 12 };

  return (
    <div>
      <Row justify="space-between" align="middle" wrap style={{ marginBottom: 16, rowGap: 12 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          Tableau de bord — ventes
        </Typography.Title>
        <Space wrap>
          <RangePicker
            value={range as any}
            format="DD/MM/YYYY"
            allowClear={false}
            onChange={(v) => v && setRange(v as [Dayjs, Dayjs])}
          />
          <Select
            placeholder="Toutes les familles"
            allowClear
            showSearch
            optionFilterProp="label"
            style={{ width: 220 }}
            value={famille}
            onChange={(v) => setFamille(v)}
            options={familles.map((f) => ({ label: f.nom, value: f.id }))}
          />
        </Space>
      </Row>

      {erreur && (
        <Alert type="warning" showIcon style={{ marginBottom: 16 }} message="Impossible de charger les données." />
      )}

      {/* KPIs */}
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Chiffre d'affaires" value={eur2.format(stats?.ca_eur ?? 0)} prefix={<EuroCircleOutlined />} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Poids vendu" value={stats?.kg ?? 0} precision={1} suffix="kg" prefix={<ShoppingOutlined />} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Panier moyen" value={eur2.format(stats?.panier_moyen ?? 0)} prefix={<ShoppingCartOutlined />} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Tickets" value={stats?.tickets ?? 0} suffix={stats ? `· ${stats.plu_distincts} PLU` : ""} prefix={<TagsOutlined />} />
          </Card>
        </Col>
      </Row>

      {/* CA par jour */}
      <Row style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="Chiffre d'affaires par jour">
            <div style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={serie} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
                  <defs>
                    <linearGradient id="grad-ca" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={t.primary} stopOpacity={0.35} />
                      <stop offset="100%" stopColor={t.primary} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid vertical={false} stroke={t.grid} />
                  <XAxis
                    dataKey="jour"
                    tick={axis}
                    tickLine={false}
                    axisLine={{ stroke: t.grid }}
                    tickFormatter={(d) => dayjs(d).format("DD/MM")}
                  />
                  <YAxis
                    tick={axis}
                    tickLine={false}
                    axisLine={false}
                    width={54}
                    tickFormatter={(v) => eur0.format(v)}
                  />
                  <Tooltip
                    contentStyle={tooltipStyle}
                    labelFormatter={(d) => dayjs(d).format("dddd DD/MM/YYYY")}
                    formatter={(v: any) => [eur2.format(v), "CA"]}
                  />
                  <Area
                    type="monotone"
                    dataKey="ca_eur"
                    stroke={t.primary}
                    strokeWidth={2}
                    fill="url(#grad-ca)"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        {/* CA par famille */}
        <Col xs={24} lg={12}>
          <Card title="CA par famille">
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={parFamille} layout="vertical" margin={{ top: 4, right: 56, bottom: 0, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke={t.grid} />
                  <XAxis type="number" tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => eur0.format(v)} />
                  <YAxis type="category" dataKey="famille" width={120} tick={axis} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: t.grid, opacity: 0.3 }} formatter={(v: any) => [eur2.format(v), "CA"]} />
                  <Bar dataKey="ca_eur" fill={t.primary} radius={[0, 4, 4, 0]} barSize={16}>
                    <LabelList dataKey="ca_eur" position="right" formatter={(v: any) => eur0.format(v)} style={{ fill: t.text, fontSize: 11 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        {/* CA par heure */}
        <Col xs={24} lg={12}>
          <Card title="CA par heure">
            <div style={{ height: 320 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={parHeure} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
                  <CartesianGrid vertical={false} stroke={t.grid} />
                  <XAxis dataKey="heure" tick={axis} tickLine={false} axisLine={{ stroke: t.grid }} interval={0} />
                  <YAxis tick={axis} tickLine={false} axisLine={false} width={54} tickFormatter={(v) => eur0.format(v)} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: t.grid, opacity: 0.3 }} formatter={(v: any) => [eur2.format(v), "CA"]} />
                  <Bar dataKey="ca_eur" fill={t.primary} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        {/* Top produits */}
        <Col xs={24} lg={12}>
          <Card title="Top produits (par CA)">
            <div style={{ height: 360 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={top} layout="vertical" margin={{ top: 4, right: 56, bottom: 0, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke={t.grid} />
                  <XAxis type="number" tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => eur0.format(v)} />
                  <YAxis type="category" dataKey="nom" width={150} tick={{ ...axis, fontSize: 11 }} tickLine={false} axisLine={false} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: t.grid, opacity: 0.3 }} formatter={(v: any) => [eur2.format(v), "CA"]} />
                  <Bar dataKey="ca_eur" fill={t.primary} radius={[0, 4, 4, 0]} barSize={14}>
                    <LabelList dataKey="ca_eur" position="right" formatter={(v: any) => eur0.format(v)} style={{ fill: t.text, fontSize: 11 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>

        {/* Par vendeur */}
        <Col xs={24} lg={12}>
          <Card title="CA par vendeur">
            <div style={{ height: 360 }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={parVendeur} layout="vertical" margin={{ top: 4, right: 56, bottom: 0, left: 8 }}>
                  <CartesianGrid horizontal={false} stroke={t.grid} />
                  <XAxis type="number" tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => eur0.format(v)} />
                  <YAxis type="category" dataKey="vendeur" width={90} tick={axis} tickLine={false} axisLine={false} tickFormatter={(v) => `Vendeur ${v}`} />
                  <Tooltip contentStyle={tooltipStyle} cursor={{ fill: t.grid, opacity: 0.3 }} formatter={(v: any) => [eur2.format(v), "CA"]} />
                  <Bar dataKey="ca_eur" fill={t.primary} radius={[0, 4, 4, 0]} barSize={20}>
                    <LabelList dataKey="ca_eur" position="right" formatter={(v: any) => eur0.format(v)} style={{ fill: t.text, fontSize: 11 }} />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </Col>
      </Row>

      {stats && stats.lignes_annulees > 0 && (
        <Typography.Paragraph type="secondary" style={{ marginTop: 12 }}>
          Annulations exclues du CA.
        </Typography.Paragraph>
      )}
    </div>
  );
};
