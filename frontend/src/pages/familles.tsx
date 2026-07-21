import { useEffect, useState } from "react";
import {
  Create,
  DeleteButton,
  Edit,
  EditButton,
  List,
  useForm,
  useTable,
} from "@refinedev/antd";
import { Form, Input, InputNumber, Space, Table } from "antd";

export const FamilleList = () => {
  const { tableProps, setFilters } = useTable({ syncWithLocation: true });
  const [search, setSearch] = useState("");
  useEffect(() => {
    setFilters(
      search ? [{ field: "nom", operator: "contains", value: search }] : [],
      "replace",
    );
  }, [search]);

  return (
    <List title="Familles">
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="Rechercher une famille…"
          allowClear
          style={{ width: 280 }}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Space>
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="code" title="Code" sorter />
        <Table.Column dataIndex="nom" title="Famille" sorter />
        <Table.Column
          dataIndex="marge_cible"
          title="Marge cible"
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

const FamilleForm = ({ formProps }: any) => (
  <Form {...formProps} layout="vertical">
    <Form.Item label="Code" name="code">
      <Input />
    </Form.Item>
    <Form.Item label="Nom" name="nom" rules={[{ required: true }]}>
      <Input />
    </Form.Item>
    <Form.Item label="Marge cible (%)" name="marge_cible">
      <InputNumber min={0} max={100} step={1} style={{ width: "100%" }} />
    </Form.Item>
  </Form>
);

export const FamilleCreate = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Create saveButtonProps={saveButtonProps}>
      <FamilleForm formProps={formProps} />
    </Create>
  );
};

export const FamilleEdit = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Edit saveButtonProps={saveButtonProps}>
      <FamilleForm formProps={formProps} />
    </Edit>
  );
};
