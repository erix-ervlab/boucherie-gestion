import { useEffect, useRef, useState } from "react";
import { RobotOutlined, SendOutlined, UserOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Collapse,
  Input,
  Space,
  Spin,
  Typography,
  theme as antdTheme,
} from "antd";

import { ModeleSelect, useModele } from "../components/ModeleSelect";

type Msg = { role: "user" | "assistant"; content: string; sql?: string[] };

const SUGGESTIONS = [
  "Quel a été mon meilleur jour de vente ?",
  "Top 5 des produits par chiffre d'affaires",
  "Répartition du CA par famille",
  "À quelles heures est-ce que je vends le plus ?",
];

export const CopilotPage = () => {
  const { token } = antdTheme.useToken();
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<{ configure: boolean; modele: string } | null>(null);
  const { modeles, modele, setModele } = useModele("copilot");
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    fetch("/api/copilot/status")
      .then((r) => r.json())
      .then(setStatus)
      .catch(() => {});
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const send = async (text?: string) => {
    const q = (text ?? input).trim();
    if (!q || loading) return;
    const next: Msg[] = [...messages, { role: "user", content: q }];
    setMessages(next);
    setInput("");
    setLoading(true);
    try {
      const r = await fetch("/api/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: next.map((m) => ({ role: m.role, content: m.content })),
          modele: modele || undefined,
        }),
      });
      if (!r.ok) {
        const e = await r.json().catch(() => ({}));
        throw new Error(e.detail || `HTTP ${r.status}`);
      }
      const data = await r.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.reponse, sql: data.requetes_sql },
      ]);
    } catch (e: any) {
      setMessages((m) => [
        ...m,
        { role: "assistant", content: "⚠️ " + (e.message || "Erreur"), sql: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const bubble = (m: Msg, i: number) => {
    const mine = m.role === "user";
    return (
      <div
        key={i}
        style={{
          display: "flex",
          justifyContent: mine ? "flex-end" : "flex-start",
          marginBottom: 12,
        }}
      >
        <div style={{ maxWidth: "80%" }}>
          <div
            style={{
              padding: "10px 14px",
              borderRadius: 12,
              background: mine ? token.colorPrimary : token.colorBgElevated,
              color: mine ? token.colorTextLightSolid : token.colorText,
              border: mine ? "none" : `1px solid ${token.colorBorderSecondary}`,
            }}
          >
            <Space size={6} style={{ marginBottom: 4, opacity: 0.8 }}>
              {mine ? <UserOutlined /> : <RobotOutlined />}
              <span style={{ fontSize: 12 }}>{mine ? "Vous" : "Copilote"}</span>
            </Space>
            <Typography.Paragraph
              style={{ whiteSpace: "pre-wrap", margin: 0, color: "inherit" }}
            >
              {m.content}
            </Typography.Paragraph>
          </div>
          {m.sql && m.sql.length > 0 && (
            <Collapse
              ghost
              size="small"
              style={{ marginTop: 4 }}
              items={[
                {
                  key: "sql",
                  label: (
                    <span style={{ fontSize: 12 }}>
                      {m.sql.length} requête(s) SQL exécutée(s)
                    </span>
                  ),
                  children: (
                    <pre
                      style={{
                        margin: 0,
                        fontSize: 12,
                        whiteSpace: "pre-wrap",
                        color: token.colorTextSecondary,
                      }}
                    >
                      {m.sql.join(";\n\n")}
                    </pre>
                  ),
                },
              ]}
            />
          )}
        </div>
      </div>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 120px)" }}>
      <Space align="center" wrap style={{ marginBottom: 8 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          <RobotOutlined /> Copilote
        </Typography.Title>
        <ModeleSelect modeles={modeles} modele={modele} setModele={setModele} />
      </Space>

      {modele === "claude-opus-4-8" && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message="Opus 4.8 sélectionné — modèle coûteux"
          description="Réservez-le aux demandes complexes (analyses détaillées, raisonnements poussés). Pour les questions courantes, Sonnet (par défaut) ou Haiku suffisent et coûtent bien moins cher."
        />
      )}

      {status && !status.configure && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 12 }}
          message="Copilote non configuré"
          description="La clé ANTHROPIC_API_KEY est absente côté serveur."
        />
      )}

      <div style={{ flex: 1, overflowY: "auto", paddingRight: 4 }}>
        {messages.length === 0 && (
          <div style={{ color: token.colorTextSecondary, marginBottom: 16 }}>
            <Typography.Paragraph type="secondary">
              Posez une question sur vos ventes en langage naturel. Le copilote
              interroge vos données (en lecture seule) et vous répond avec une
              analyse.
            </Typography.Paragraph>
            <Space wrap>
              {SUGGESTIONS.map((s) => (
                <Button key={s} size="small" onClick={() => send(s)}>
                  {s}
                </Button>
              ))}
            </Space>
          </div>
        )}
        {messages.map(bubble)}
        {loading && (
          <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
            <Space style={{ color: token.colorTextSecondary }}>
              <Spin size="small" /> Le copilote réfléchit et interroge les données…
            </Space>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <Space.Compact style={{ marginTop: 12 }}>
        <Input.TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ex : compare mes ventes de bœuf et de porc cette semaine"
          autoSize={{ minRows: 1, maxRows: 4 }}
          onPressEnter={(e) => {
            if (!e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          disabled={loading || (status ? !status.configure : false)}
        />
        <Button
          type="primary"
          icon={<SendOutlined />}
          onClick={() => send()}
          loading={loading}
          disabled={status ? !status.configure : false}
        >
          Envoyer
        </Button>
      </Space.Compact>
    </div>
  );
};
