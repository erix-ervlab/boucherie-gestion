import {
  DashboardOutlined,
  ShopOutlined,
  AppstoreOutlined,
  TeamOutlined,
  UploadOutlined,
  RobotOutlined,
  ContainerOutlined,
  PercentageOutlined,
  HistoryOutlined,
  LinkOutlined,
  AreaChartOutlined,
  ScissorOutlined,
  ExperimentOutlined,
  FundOutlined,
  ShoppingOutlined,
  ProfileOutlined,
  DatabaseOutlined,
  QuestionCircleOutlined,
  ReadOutlined,
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
import { MargePage } from "./pages/marge";
import { HistoriquePage } from "./pages/historique";
import { GrafanaPage } from "./pages/grafana";
import { ImportsPage } from "./pages/imports";
import { ProduitCreate, ProduitEdit, ProduitList } from "./pages/produits";
import { FamilleCreate, FamilleEdit, FamilleList } from "./pages/familles";
import {
  FournisseurCreate,
  FournisseurEdit,
  FournisseurList,
} from "./pages/fournisseurs";
import {
  CorrespondanceCreate,
  CorrespondanceEdit,
  CorrespondanceList,
} from "./pages/correspondances";
import { GammeCreate, GammeEdit, GammeList } from "./pages/gammes";
import { RendementPage } from "./pages/rendement";
import { DocumentationPage } from "./pages/documentation";

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
              // ── Pilotage ─────────────────────────────────────────────
              {
                name: "grp_pilotage",
                meta: { label: "Pilotage", icon: <FundOutlined /> },
              },
              {
                name: "dashboard",
                list: "/",
                meta: {
                  parent: "grp_pilotage",
                  label: "Tableau de bord",
                  icon: <DashboardOutlined />,
                },
              },
              {
                name: "copilot",
                list: "/copilot",
                meta: {
                  parent: "grp_pilotage",
                  label: "Copilote",
                  icon: <RobotOutlined />,
                },
              },
              {
                name: "marge",
                list: "/marge",
                meta: {
                  parent: "grp_pilotage",
                  label: "Marge",
                  icon: <PercentageOutlined />,
                },
              },
              {
                name: "rendement",
                list: "/rendement",
                meta: {
                  parent: "grp_pilotage",
                  label: "Rendement",
                  icon: <ExperimentOutlined />,
                },
              },
              {
                name: "exploration",
                list: "/exploration",
                meta: {
                  parent: "grp_pilotage",
                  label: "Exploration (Grafana)",
                  icon: <AreaChartOutlined />,
                },
              },
              // ── Achats & fournisseurs ────────────────────────────────
              {
                name: "grp_achats",
                meta: {
                  label: "Achats & fournisseurs",
                  icon: <ShoppingOutlined />,
                },
              },
              {
                name: "achats",
                list: "/achats",
                meta: {
                  parent: "grp_achats",
                  label: "Achats",
                  icon: <ContainerOutlined />,
                },
              },
              {
                name: "fournisseurs",
                list: "/fournisseurs",
                create: "/fournisseurs/create",
                edit: "/fournisseurs/edit/:id",
                meta: {
                  parent: "grp_achats",
                  label: "Fournisseurs",
                  icon: <TeamOutlined />,
                },
              },
              {
                name: "correspondances",
                list: "/correspondances",
                create: "/correspondances/create",
                edit: "/correspondances/edit/:id",
                meta: {
                  parent: "grp_achats",
                  label: "Correspondances",
                  icon: <LinkOutlined />,
                },
              },
              {
                name: "gammes",
                list: "/gammes",
                create: "/gammes/create",
                edit: "/gammes/edit/:id",
                meta: {
                  parent: "grp_achats",
                  label: "Gammes de découpe",
                  icon: <ScissorOutlined />,
                },
              },
              // ── Catalogue ────────────────────────────────────────────
              {
                name: "grp_catalogue",
                meta: { label: "Catalogue", icon: <ProfileOutlined /> },
              },
              {
                name: "produits",
                list: "/produits",
                create: "/produits/create",
                edit: "/produits/edit/:id",
                meta: {
                  parent: "grp_catalogue",
                  label: "Produits (PLU)",
                  icon: <ShopOutlined />,
                },
              },
              {
                name: "familles",
                list: "/familles",
                create: "/familles/create",
                edit: "/familles/edit/:id",
                meta: {
                  parent: "grp_catalogue",
                  label: "Familles",
                  icon: <AppstoreOutlined />,
                },
              },
              // ── Données & journal ────────────────────────────────────
              {
                name: "grp_donnees",
                meta: {
                  label: "Données & journal",
                  icon: <DatabaseOutlined />,
                },
              },
              {
                name: "imports",
                list: "/imports",
                meta: {
                  parent: "grp_donnees",
                  label: "Import caisse",
                  icon: <UploadOutlined />,
                },
              },
              {
                name: "historique",
                list: "/historique",
                meta: {
                  parent: "grp_donnees",
                  label: "Historique",
                  icon: <HistoryOutlined />,
                },
              },
              // ── Aide ─────────────────────────────────────────────────
              {
                name: "grp_aide",
                meta: { label: "Aide", icon: <QuestionCircleOutlined /> },
              },
              {
                name: "documentation",
                list: "/documentation",
                meta: {
                  parent: "grp_aide",
                  label: "Documentation",
                  icon: <ReadOutlined />,
                },
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
                <Route path="/marge" element={<MargePage />} />
                <Route path="/rendement" element={<RendementPage />} />
                <Route path="/imports" element={<ImportsPage />} />
                <Route path="/historique" element={<HistoriquePage />} />
                <Route path="/exploration" element={<GrafanaPage />} />
                <Route path="/documentation" element={<DocumentationPage />} />
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
                <Route path="/correspondances">
                  <Route index element={<CorrespondanceList />} />
                  <Route path="create" element={<CorrespondanceCreate />} />
                  <Route path="edit/:id" element={<CorrespondanceEdit />} />
                </Route>
                <Route path="/gammes">
                  <Route index element={<GammeList />} />
                  <Route path="create" element={<GammeCreate />} />
                  <Route path="edit/:id" element={<GammeEdit />} />
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
