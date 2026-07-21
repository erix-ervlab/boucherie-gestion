import { useList } from "@refinedev/core";
import {
  Create,
  DeleteButton,
  Edit,
  EditButton,
  List,
  useForm,
  useSelect,
  useTable,
} from "@refinedev/antd";
import { Form, Input, InputNumber, Select, Space, Switch, Table } from "antd";

const UNITES = [
  { label: "Kg", value: "Kg" },
  { label: "Pièce", value: "Pièce" },
];

const useFamilleMap = () => {
  const { data } = useList({ resource: "familles", pagination: { mode: "off" } });
  const map: Record<number, string> = {};
  (data?.data ?? []).forEach((f: any) => (map[f.id] = f.nom));
  return map;
};

export const ProduitList = () => {
  const { tableProps } = useTable({ syncWithLocation: true });
  const famMap = useFamilleMap();

  return (
    <List title="Produits (PLU)">
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="code_plu" title="PLU" sorter />
        <Table.Column dataIndex="nom" title="Produit" sorter />
        <Table.Column
          dataIndex="famille_id"
          title="Famille"
          render={(id: number) => famMap[id] ?? id ?? "—"}
        />
        <Table.Column
          dataIndex="prix_vente"
          title="Prix TTC"
          align="right"
          render={(v: any) => (v != null ? `${v} €` : "—")}
        />
        <Table.Column dataIndex="unite" title="Unité" />
        <Table.Column
          dataIndex="tva"
          title="TVA"
          align="right"
          render={(v: any) => (v != null ? `${v} %` : "—")}
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

const ProduitForm = ({ formProps }: any) => {
  const { selectProps: familleSelect } = useSelect({
    resource: "familles",
    optionLabel: "nom",
    optionValue: "id",
    pagination: { mode: "off" },
  });

  return (
    <Form {...formProps} layout="vertical">
      <Form.Item label="Code PLU" name="code_plu" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item label="Produit" name="nom" rules={[{ required: true }]}>
        <Input />
      </Form.Item>
      <Form.Item label="Famille" name="famille_id">
        <Select {...familleSelect} allowClear placeholder="Choisir une famille" />
      </Form.Item>
      <Form.Item label="Prix de vente TTC (€)" name="prix_vente">
        <InputNumber min={0} step={0.01} style={{ width: "100%" }} />
      </Form.Item>
      <Form.Item label="Unité" name="unite">
        <Select options={UNITES} allowClear />
      </Form.Item>
      <Form.Item label="TVA (%)" name="tva">
        <InputNumber min={0} max={100} step={0.5} style={{ width: "100%" }} />
      </Form.Item>
      <Form.Item label="Actif" name="actif" valuePropName="checked" initialValue={true}>
        <Switch />
      </Form.Item>
    </Form>
  );
};

export const ProduitCreate = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Create saveButtonProps={saveButtonProps}>
      <ProduitForm formProps={formProps} />
    </Create>
  );
};

export const ProduitEdit = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Edit saveButtonProps={saveButtonProps}>
      <ProduitForm formProps={formProps} />
    </Edit>
  );
};
