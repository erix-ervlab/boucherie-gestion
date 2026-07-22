import { useMemo, useState } from "react";
import { Card, Col, Empty, Input, Menu, Row, Typography } from "antd";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

import { DOCS } from "../docs/content";

/** Documentation intégrée : liste des sections + recherche + rendu Markdown. */
export const DocumentationPage = () => {
  const [current, setCurrent] = useState<string>(DOCS[0].id);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return DOCS;
    return DOCS.filter(
      (d) =>
        d.title.toLowerCase().includes(q) || d.body.toLowerCase().includes(q),
    );
  }, [search]);

  // Si la recherche masque la section courante, bascule sur le 1er résultat.
  const active =
    filtered.find((d) => d.id === current)?.id ?? filtered[0]?.id ?? "";
  const section = DOCS.find((d) => d.id === active);

  return (
    <Row gutter={16}>
      <Col xs={24} md={7} lg={6}>
        <Card size="small" title="Documentation" style={{ marginBottom: 16 }}>
          <Input.Search
            placeholder="Rechercher dans l'aide…"
            allowClear
            style={{ marginBottom: 12 }}
            onChange={(e) => setSearch(e.target.value)}
          />
          {filtered.length ? (
            <Menu
              mode="inline"
              selectedKeys={[active]}
              style={{ border: "none" }}
              onClick={({ key }) => setCurrent(key)}
              items={filtered.map((d) => ({ key: d.id, label: d.title }))}
            />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="Aucune section"
            />
          )}
        </Card>
      </Col>

      <Col xs={24} md={17} lg={18}>
        <Card>
          {section ? (
            <div className="doc-md">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {section.body}
              </ReactMarkdown>
            </div>
          ) : (
            <Typography.Text type="secondary">
              Sélectionnez une section.
            </Typography.Text>
          )}
        </Card>
      </Col>

      {/* Styles du Markdown rendu (titres, tableaux, code, citations). */}
      <style>{`
        .doc-md { line-height: 1.6; font-size: 14px; }
        .doc-md h1 { font-size: 24px; margin: 0 0 16px; }
        .doc-md h2 { font-size: 19px; margin: 24px 0 10px; }
        .doc-md h3 { font-size: 16px; margin: 18px 0 8px; }
        .doc-md p { margin: 8px 0; }
        .doc-md ul, .doc-md ol { padding-left: 22px; margin: 8px 0; }
        .doc-md li { margin: 4px 0; }
        .doc-md code {
          background: rgba(135,131,120,.15); padding: 1px 5px;
          border-radius: 4px; font-size: 90%;
        }
        .doc-md table { border-collapse: collapse; margin: 12px 0; width: 100%; }
        .doc-md th, .doc-md td {
          border: 1px solid rgba(128,128,128,.35); padding: 6px 10px;
          text-align: left;
        }
        .doc-md th { background: rgba(128,128,128,.12); }
        .doc-md blockquote {
          margin: 12px 0; padding: 8px 14px;
          border-left: 3px solid #d4380d;
          background: rgba(212,56,13,.06); border-radius: 4px;
        }
        .doc-md blockquote p { margin: 4px 0; }
        .doc-md a { color: #d4380d; }
      `}</style>
    </Row>
  );
};
