import { Layout, theme as antdTheme } from "antd";

import { ThemeSwitcher } from "./ThemeSwitcher";

export const Header = () => {
  const { token } = antdTheme.useToken();
  return (
    <Layout.Header
      style={{
        display: "flex",
        justifyContent: "flex-end",
        alignItems: "center",
        gap: 12,
        padding: "0 24px",
        height: 64,
        position: "sticky",
        top: 0,
        zIndex: 10,
        background: token.colorBgElevated,
        borderBottom: `1px solid ${token.colorBorderSecondary}`,
      }}
    >
      <ThemeSwitcher />
    </Layout.Header>
  );
};
