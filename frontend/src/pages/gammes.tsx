import { useEffect, useMemo, useState } from "react";
import {
  useCreate,
  useList,
  useNavigation,
  useOne,
  useUpdate,
} from "@refinedev/core";
import {
  DeleteButton,
  EditButton,
  List,
  useTable,
} from "@refinedev/antd";
import {
  Alert,
  Button,
  Card,
  Input,
  InputNumber,
  Select,
  Space,
  Switch,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import { DeleteOutlined, PlusOutlined } from "@ant-design/icons";
import { useParams } from "react-router-dom";

type Sortie = { produit_id?: number; rendement_pct?: number };

function useProduits() {
  const { data } = useList({
    resource: "produits",
    pagination: { pageSize: 1000 },
  });
  const produits = (data?.data ?? []) as any[];
  const options = produits.map((p) => ({
    value: p.id,
    label: `${p.code_plu} — ${p.nom}`,
  }));
  return { produits, options };
}

export const GammeList = () => {
  const { tableProps } = useTable({
    syncWithLocation: true,
    sorters: { initial: [{ field: "nom", order: "asc" }] },
  });
  return (
    <List title="Gammes de découpe (rendement théorique)">
      <Typography.Paragraph type="secondary">
        Une gamme décrit l'éclatement d'un morceau transformé en PLU vendus. Le
        reste (100 − Σ rendements) est la perte (os, gras, chutes). Reliez
        ensuite une référence d'achat à sa gamme depuis « Correspondances ».
      </Typography.Paragraph>
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="nom" title="Morceau" sorter />
        <Table.Column
          dataIndex="sorties"
          title="PLU produits"
          render={(v: any[]) => v?.length ?? 0}
        />
        <Table.Column
          dataIndex="rendement_total"
          title="Rendement"
          render={(v: number) => `${Number(v ?? 0).toFixed(0)} %`}
        />
        <Table.Column
          dataIndex="perte_pct"
          title="Perte"
          render={(v: number) => (
            <Tag color={Number(v) < 0 ? "red" : "orange"}>
              {Number(v ?? 0).toFixed(0)} %
            </Tag>
          )}
        />
        <Table.Column
          dataIndex="actif"
          title="Actif"
          render={(v: boolean) =>
            v ? <Tag color="green">actif</Tag> : <Tag>inactif</Tag>
          }
        />
        <Table.Column
          title="Actions"
          dataIndex="actions"
          render={(_, r: any) => (
            <Space>
              <EditButton hideText size="small" recordItemId={r.id} />
              <DeleteButton hideText size="small" recordItemId={r.id} />
            </Space>
          )}
        />
      </Table>
    </List>
  );
};

const GammeForm = ({ id }: { id?: number }) => {
  const { options } = useProduits();
  const [nom, setNom] = useState("");
  const [note, setNote] = useState("");
  const [actif, setActif] = useState(true);
  const [sorties, setSorties] = useState<Sortie[]>([{}]);
  const { list } = useNavigation();
  const { mutate: create, isLoading: creating } = useCreate();
  const { mutate: update, isLoading: updating } = useUpdate();

  const { data: one } = useOne({
    resource: "gammes",
    id: id as number,
    queryOptions: { enabled: !!id },
  });
  useEffect(() => {
    const g: any = one?.data;
    if (g) {
      setNom(g.nom ?? "");
      setNote(g.note ?? "");
      setActif(g.actif ?? true);
      setSorties(
        (g.sorties ?? []).map((s: any) => ({
          produit_id: s.produit_id,
          rendement_pct: Number(s.rendement_pct),
        })),
      );
    }
  }, [one]);

  const total = sorties.reduce((a, s) => a + (Number(s.rendement_pct) || 0), 0);
  const perte = 100 - total;

  const setRow = (i: number, patch: Partial<Sortie>) =>
    setSorties((prev) => prev.map((s, j) => (j === i ? { ...s, ...patch } : s)));

  const submit = () => {
    if (!nom.trim()) return message.error("Le nom du morceau est requis.");
    if (total > 100)
      return message.error("La somme des rendements dépasse 100 %.");
    const values = {
      nom,
      note,
      actif,
      sorties: sorties
        .filter((s) => s.produit_id)
        .map((s) => ({
          produit_id: s.produit_id,
          rendement_pct: Number(s.rendement_pct) || 0,
        })),
    };
    const opts = {
      onSuccess: () => {
        message.success("Gamme enregistrée.");
        list("gammes");
      },
      onError: (e: any) => message.error(e?.message ?? "Erreur"),
    };
    if (id) update({ resource: "gammes", id, values }, opts);
    else create({ resource: "gammes", values }, opts);
  };

  return (
    <Card title={id ? "Modifier la gamme" : "Nouvelle gamme de découpe"}>
      <Space direction="vertical" style={{ width: "100%" }} size="middle">
        <Space wrap>
          <Input
            placeholder="Morceau (ex. Arrière de veau)"
            value={nom}
            onChange={(e) => setNom(e.target.value)}
            style={{ width: 320 }}
          />
          <span>
            Actif{" "}
            <Switch checked={actif} onChange={setActif} size="small" />
          </span>
        </Space>
        <Input
          placeholder="Note (optionnel)"
          value={note}
          onChange={(e) => setNote(e.target.value)}
        />

        <Table
          dataSource={sorties.map((s, i) => ({ ...s, key: i }))}
          rowKey="key"
          size="small"
          pagination={false}
        >
          <Table.Column
            title="PLU produit"
            render={(_, __, i: number) => (
              <Select
                showSearch
                optionFilterProp="label"
                placeholder="Choisir un PLU…"
                style={{ width: 340 }}
                options={options}
                value={sorties[i].produit_id}
                onChange={(v) => setRow(i, { produit_id: v })}
              />
            )}
          />
          <Table.Column
            title="Rendement %"
            width={140}
            render={(_, __, i: number) => (
              <InputNumber
                min={0}
                max={100}
                step={1}
                value={sorties[i].rendement_pct}
                onChange={(v) => setRow(i, { rendement_pct: v ?? undefined })}
                addonAfter="%"
              />
            )}
          />
          <Table.Column
            title=""
            width={50}
            render={(_, __, i: number) => (
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
                onClick={() =>
                  setSorties((prev) => prev.filter((_, j) => j !== i))
                }
              />
            )}
          />
        </Table>

        <Button
          icon={<PlusOutlined />}
          onClick={() => setSorties((prev) => [...prev, {}])}
        >
          Ajouter un PLU
        </Button>

        <Alert
          type={total > 100 ? "error" : "info"}
          showIcon
          message={
            <span>
              Rendement total : <b>{total.toFixed(0)} %</b> · Perte (os, gras,
              chutes) : <b>{perte.toFixed(0)} %</b>
              {total > 100 && " — dépasse 100 % !"}
            </span>
          }
        />

        <Space>
          <Button
            type="primary"
            onClick={submit}
            loading={creating || updating}
          >
            Enregistrer
          </Button>
          <Button onClick={() => list("gammes")}>Annuler</Button>
        </Space>
      </Space>
    </Card>
  );
};

export const GammeCreate = () => <GammeForm />;

export const GammeEdit = () => {
  const { id } = useParams();
  return <GammeForm id={id ? Number(id) : undefined} />;
};
