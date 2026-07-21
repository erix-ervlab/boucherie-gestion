import {
  DashboardOutlined,
  ShopOutlined,
  AppstoreOutlined,
  TeamOutlined,
  UploadOutlined,
  RobotOutlined,
  ContainerOutlined,
} from "@ant-design/icons";
import { Refine } from "@refinedev/core";
import {
  ErrorComponent,
  ThemedLayoutV2,
  ThemedTitleV2,
  useNotificationProvider,
} from "@refinedev/antd";
import "@refinedev/antd/dist/reset.css";
import dataProvider from "@refinedev/simple-rest";
import routerBindings, {
  DocumentTitleHandler,
  UnsavedChangesNotifier,
} from "@refinedev/react-router-v6";
import { App as AntdApp } from "antd";
import { BrowserRouter, Outlet, Route, Routes } from "react-router-dom";

import { Header } from "./components/Header";
import { ThemeProvider } from "./theme";
import { Dashboard } from "./pages/dashboard";
import { CopilotPage } from "./pages/copilot";
import { AchatsPage } from "./pages/achats";
import { ImportsPage } from "./pages/imports";
import { ProduitCreate, ProduitEdit, ProduitList } from "./pages/produits";
import { FamilleCreate, FamilleEdit, FamilleList } from "./pages/familles";
import {
  FournisseurCreate,
  FournisseurEdit,
  FournisseurList,
} from "./pages/fournisseurs";

const API_URL = "/api";

function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AntdApp>
          <Refine
            dataProvider={dataProvider(API_URL)}
            routerProvider={routerBindings}
            notificationProvider={useNotificationProvider}
            resources={[
              {
                name: "dashboard",
                list: "/",
                meta: { label: "Tableau de bord", icon: <DashboardOutlined /> },
              },
              {
                name: "copilot",
                list: "/copilot",
                meta: { label: "Copilote", icon: <RobotOutlined /> },
              },
              {
                name: "achats",
                list: "/achats",
                meta: { label: "Achats", icon: <ContainerOutlined /> },
              },
              {
                name: "imports",
                list: "/imports",
                meta: { label: "Import caisse", icon: <UploadOutlined /> },
              },
              {
                name: "produits",
                list: "/produits",
                create: "/produits/create",
                edit: "/produits/edit/:id",
                meta: { label: "Produits (PLU)", icon: <ShopOutlined /> },
              },
              {
                name: "familles",
                list: "/familles",
                create: "/familles/create",
                edit: "/familles/edit/:id",
                meta: { label: "Familles", icon: <AppstoreOutlined /> },
              },
              {
                name: "fournisseurs",
                list: "/fournisseurs",
                create: "/fournisseurs/create",
                edit: "/fournisseurs/edit/:id",
                meta: { label: "Fournisseurs", icon: <TeamOutlined /> },
              },
            ]}
            options={{
              syncWithLocation: true,
              warnWhenUnsavedChanges: true,
            }}
          >
            <Routes>
              <Route
                element={
                  <ThemedLayoutV2
                    Header={Header}
                    Title={({ collapsed }) => (
                      <ThemedTitleV2
                        collapsed={collapsed}
                        text="Abbatiale"
                        icon={<ShopOutlined />}
                      />
                    )}
                  >
                    <Outlet />
                  </ThemedLayoutV2>
                }
              >
                <Route index element={<Dashboard />} />
                <Route path="/copilot" element={<CopilotPage />} />
                <Route path="/achats" element={<AchatsPage />} />
                <Route path="/imports" element={<ImportsPage />} />
                <Route path="/produits">
                  <Route index element={<ProduitList />} />
                  <Route path="create" element={<ProduitCreate />} />
                  <Route path="edit/:id" element={<ProduitEdit />} />
                </Route>
                <Route path="/familles">
                  <Route index element={<FamilleList />} />
                  <Route path="create" element={<FamilleCreate />} />
                  <Route path="edit/:id" element={<FamilleEdit />} />
                </Route>
                <Route path="/fournisseurs">
                  <Route index element={<FournisseurList />} />
                  <Route path="create" element={<FournisseurCreate />} />
                  <Route path="edit/:id" element={<FournisseurEdit />} />
                </Route>
                <Route path="*" element={<ErrorComponent />} />
              </Route>
            </Routes>
            <UnsavedChangesNotifier />
            <DocumentTitleHandler />
          </Refine>
        </AntdApp>
      </ThemeProvider>
    </BrowserRouter>
  );
}

export default App;
