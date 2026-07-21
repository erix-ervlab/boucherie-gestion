import { useEffect, useMemo, useState } from "react";
import { useList } from "@refinedev/core";
import {
  Create,
  DeleteButton,
  Edit,
  EditButton,
  List,
  useForm,
  useTable,
} from "@refinedev/antd";
import { Form, Input, Select, Space, Table, Tag } from "antd";

/** Charge les référentiels (petits) et fournit les correspondances id -> nom. */
function useRefs() {
  const { data: fData } = useList({
    resource: "fournisseurs",
    pagination: { pageSize: 500 },
  });
  const { data: famData } = useList({
    resource: "familles",
    pagination: { pageSize: 500 },
  });
  const fournisseurs = (fData?.data ?? []) as any[];
  const familles = (famData?.data ?? []) as any[];
  const fmap = useMemo(
    () => Object.fromEntries(fournisseurs.map((f) => [f.id, f.nom])),
    [fournisseurs],
  );
  const famMap = useMemo(
    () => Object.fromEntries(familles.map((f) => [f.id, f.nom])),
    [familles],
  );
  return { fournisseurs, familles, fmap, famMap };
}

export const CorrespondanceList = () => {
  const { tableProps, setFilters } = useTable({
    syncWithLocation: true,
    sorters: { initial: [{ field: "reference_fournisseur", order: "asc" }] },
  });
  const { fournisseurs, fmap, famMap } = useRefs();
  const [search, setSearch] = useState("");
  const [fourn, setFourn] = useState<number | undefined>();

  useEffect(() => {
    const filters: any[] = [];
    if (search)
      filters.push({
        field: "reference_fournisseur",
        operator: "contains",
        value: search,
      });
    if (fourn)
      filters.push({ field: "fournisseur_id", operator: "eq", value: fourn });
    setFilters(filters, "replace");
  }, [search, fourn]);

  return (
    <List title="Correspondances apprises (réf fournisseur → famille)">
      <Space style={{ marginBottom: 16 }} wrap>
        <Select
          allowClear
          showSearch
          optionFilterProp="label"
          placeholder="Filtrer par fournisseur"
          style={{ width: 240 }}
          options={fournisseurs.map((f) => ({ value: f.id, label: f.nom }))}
          onChange={(v) => setFourn(v)}
        />
        <Input.Search
          placeholder="Rechercher une référence…"
          allowClear
          style={{ width: 260 }}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Space>
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column
          dataIndex="fournisseur_id"
          title="Fournisseur"
          sorter
          render={(v: number) => fmap[v] ?? v}
        />
        <Table.Column dataIndex="reference_fournisseur" title="Référence" sorter />
        <Table.Column dataIndex="designation" title="Désignation" />
        <Table.Column
          dataIndex="famille_id"
          title="Famille"
          render={(v: number | null) =>
            v ? <Tag color="blue">{famMap[v] ?? v}</Tag> : <Tag>—</Tag>
          }
        />
        <Table.Column
          title="Actions"
          dataIndex="actions"
          render={(_, record: any) => (
            <Space>
              <EditButton hideText size="small" recordItemId={record.id} />
              <DeleteButton hideText size="small" recordItemId={record.id} />
            </Space>
          )}
        />
      </Table>
    </List>
  );
};

const CorrespondanceForm = ({ formProps }: any) => {
  const { fournisseurs, familles } = useRefs();
  return (
    <Form {...formProps} layout="vertical">
      <Form.Item
        label="Fournisseur"
        name="fournisseur_id"
        rules={[{ required: true }]}
      >
        <Select
          showSearch
          optionFilterProp="label"
          options={fournisseurs.map((f) => ({ value: f.id, label: f.nom }))}
        />
      </Form.Item>
      <Form.Item
        label="Référence fournisseur"
        name="reference_fournisseur"
        rules={[{ required: true }]}
      >
        <Input placeholder="ex. 233001-00" />
      </Form.Item>
      <Form.Item label="Désignation" name="designation">
        <Input placeholder="libellé de l'article (pour info)" />
      </Form.Item>
      <Form.Item label="Famille" name="famille_id">
        <Select
          allowClear
          showSearch
          optionFilterProp="label"
          options={familles.map((f) => ({ value: f.id, label: f.nom }))}
        />
      </Form.Item>
    </Form>
  );
};

export const CorrespondanceCreate = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Create saveButtonProps={saveButtonProps}>
      <CorrespondanceForm formProps={formProps} />
    </Create>
  );
};

export const CorrespondanceEdit = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Edit saveButtonProps={saveButtonProps}>
      <CorrespondanceForm formProps={formProps} />
    </Edit>
  );
};
