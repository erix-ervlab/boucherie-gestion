#!/bin/bash
# Crée un rôle Postgres LECTURE SEULE pour Grafana (exécuté par
# l'entrypoint Postgres au tout premier init d'un volume vierge).
# Pour une base déjà initialisée, jouer le même SQL à la main
# (voir README, section Grafana).
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
	DO \$\$ BEGIN
	  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana_ro') THEN
	    CREATE ROLE grafana_ro LOGIN PASSWORD '${GRAFANA_DB_PASSWORD}';
	  ELSE
	    ALTER ROLE grafana_ro PASSWORD '${GRAFANA_DB_PASSWORD}';
	  END IF;
	END \$\$;

	GRANT CONNECT ON DATABASE "$POSTGRES_DB" TO grafana_ro;
	GRANT USAGE ON SCHEMA public TO grafana_ro;
	GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_ro;
	-- Les tables sont créées ensuite par l'app (rôle $POSTGRES_USER) :
	-- ce défaut garantit l'accès en lecture aux tables futures.
	ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_ro;
EOSQL
