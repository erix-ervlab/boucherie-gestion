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
import { Form, Input, Space, Switch, Table, Tag } from "antd";

export const FournisseurList = () => {
  const { tableProps, setFilters } = useTable({ syncWithLocation: true });
  const [search, setSearch] = useState("");
  useEffect(() => {
    setFilters(
      search ? [{ field: "nom", operator: "contains", value: search }] : [],
      "replace",
    );
  }, [search]);

  return (
    <List title="Fournisseurs">
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="Rechercher un fournisseur…"
          allowClear
          style={{ width: 280 }}
          onChange={(e) => setSearch(e.target.value)}
        />
      </Space>
      <Table {...tableProps} rowKey="id" size="small">
        <Table.Column dataIndex="nom" title="Fournisseur" sorter />
        <Table.Column
          dataIndex="actif"
          title="Actif"
          render={(v: boolean) =>
            v ? <Tag color="green">Actif</Tag> : <Tag>Inactif</Tag>
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

const FournisseurForm = ({ formProps }: any) => (
  <Form {...formProps} layout="vertical">
    <Form.Item label="Nom" name="nom" rules={[{ required: true }]}>
      <Input />
    </Form.Item>
    <Form.Item label="Actif" name="actif" valuePropName="checked" initialValue={true}>
      <Switch />
    </Form.Item>
  </Form>
);

export const FournisseurCreate = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Create saveButtonProps={saveButtonProps}>
      <FournisseurForm formProps={formProps} />
    </Create>
  );
};

export const FournisseurEdit = () => {
  const { formProps, saveButtonProps } = useForm();
  return (
    <Edit saveButtonProps={saveButtonProps}>
      <FournisseurForm formProps={formProps} />
    </Edit>
  );
};
