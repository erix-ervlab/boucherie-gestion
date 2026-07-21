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
  const { tableProps } = useTable({ syncWithLocation: true });
  return (
    <List title="Fournisseurs">
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
