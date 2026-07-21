import { BgColorsOutlined, BulbFilled, BulbOutlined } from "@ant-design/icons";
import { Button, Dropdown, Space, Tooltip } from "antd";

import { PRESETS, colorOf, useThemeMode } from "../theme";

const swatch = (color: string) => (
  <span
    style={{
      display: "inline-block",
      width: 14,
      height: 14,
      borderRadius: 3,
      background: color,
      border: "1px solid rgba(0,0,0,0.15)",
    }}
  />
);

export const ThemeSwitcher = () => {
  const { colorKey, mode, setColorKey, toggleMode } = useThemeMode();

  const items = PRESETS.map((p) => ({
    key: p.key,
    label: (
      <Space>
        {swatch(colorOf(p.key))}
        {p.label}
      </Space>
    ),
  }));

  return (
    <Space>
      <Dropdown
        trigger={["click"]}
        menu={{
          items,
          selectable: true,
          selectedKeys: [colorKey],
          onClick: ({ key }) => setColorKey(key),
        }}
      >
        <Button icon={<BgColorsOutlined />}>Thème</Button>
      </Dropdown>
      <Tooltip title={mode === "dark" ? "Passer en clair" : "Passer en sombre"}>
        <Button
          shape="circle"
          icon={mode === "dark" ? <BulbFilled /> : <BulbOutlined />}
          onClick={toggleMode}
        />
      </Tooltip>
    </Space>
  );
};
