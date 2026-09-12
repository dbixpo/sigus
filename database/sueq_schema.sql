-- Schema SUEQ gerado do backup de produção (10/09/2026)
-- Fonte: Desktop/patrick/schema.sql  |  projeto qpvgpfwuurqcqprnpxua
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;
CREATE SCHEMA IF NOT EXISTS sueq;
SET search_path TO sueq, public;

CREATE SEQUENCE IF NOT EXISTS "sueq"."chamados_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE IF NOT EXISTS "sueq"."portal_transferencias_inventario" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "inventario_origem_id" "uuid" NOT NULL,
    "unidade_origem_id" bigint NOT NULL,
    "unidade_destino_id" bigint NOT NULL,
    "item" "jsonb" NOT NULL,
    "status" "text" DEFAULT 'PENDENTE'::"text" NOT NULL,
    "enviado_por" "uuid" NOT NULL,
    "enviado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "recebido_por" "uuid",
    "recebido_em" timestamp with time zone,
    "sala_destino_id" "uuid",
    "cancelado_por" "uuid",
    "cancelado_em" timestamp with time zone,
    CONSTRAINT "portal_transferencias_cancelamento_consistente_ck" CHECK (((("status" = 'CANCELADA'::"text") AND ("cancelado_por" IS NOT NULL) AND ("cancelado_em" IS NOT NULL) AND ("recebido_por" IS NULL) AND ("recebido_em" IS NULL) AND ("sala_destino_id" IS NULL)) OR (("status" <> 'CANCELADA'::"text") AND ("cancelado_por" IS NULL) AND ("cancelado_em" IS NULL)))),
    CONSTRAINT "portal_transferencias_inventario_status_check" CHECK (("status" = ANY (ARRAY['PENDENTE'::"text", 'RECEBIDA'::"text", 'CANCELADA'::"text"]))),
    CONSTRAINT "portal_transferencias_recebimento_consistente_ck" CHECK ((("status" <> 'RECEBIDA'::"text") OR (("recebido_por" IS NOT NULL) AND ("recebido_em" IS NOT NULL) AND ("sala_destino_id" IS NOT NULL)))),
    CONSTRAINT "portal_transferencias_unidades_distintas_ck" CHECK (("unidade_origem_id" <> "unidade_destino_id"))
);

CREATE TABLE IF NOT EXISTS "sueq"."portal_inventario" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "unidade_id" bigint NOT NULL,
    "sala_id" "uuid" NOT NULL,
    "item_nome" "text" NOT NULL,
    "categoria" "text",
    "quantidade" integer DEFAULT 1 NOT NULL,
    "patrimonio" "text",
    "numero_serie" "text",
    "marca" "text",
    "modelo" "text",
    "estado" "text" DEFAULT 'BOM'::"text" NOT NULL,
    "observacoes" "text",
    "ativo" boolean DEFAULT true NOT NULL,
    "criado_por" "uuid",
    "atualizado_por" "uuid",
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "atualizado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "inservivel_em" timestamp with time zone,
    "inservivel_por" "uuid",
    CONSTRAINT "portal_inventario_estado_check" CHECK (("estado" = ANY (ARRAY['NOVO'::"text", 'BOM'::"text", 'REGULAR'::"text", 'RUIM'::"text", 'INSERVIVEL'::"text"]))),
    CONSTRAINT "portal_inventario_item_nome_check" CHECK ((("length"(TRIM(BOTH FROM "item_nome")) >= 2) AND ("length"(TRIM(BOTH FROM "item_nome")) <= 180))),
    CONSTRAINT "portal_inventario_quantidade_check" CHECK (("quantidade" > 0)),
    CONSTRAINT "portal_inventario_quantidade_uma_unidade_ck" CHECK (("quantidade" = 1))
);

CREATE TABLE IF NOT EXISTS "sueq"."notas_fiscais" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "numero" "text" NOT NULL,
    "numero_normalizado" "text",
    "serie" "text",
    "chave_acesso" "text",
    "fornecedor_id" bigint,
    "contrato_id" integer,
    "processo_id" bigint,
    "emenda_id" "uuid",
    "data_emissao" "date",
    "data_recebimento" "date",
    "valor_total" numeric,
    "valor_bruto" numeric,
    "valor_liquido" numeric,
    "retencoes" numeric,
    "competencia" "text",
    "status" "text" DEFAULT 'recebida'::"text",
    "origem_sistema" "text",
    "origem_codigo" "text",
    "raw_data" "jsonb",
    "arquivo_url" "text",
    "observacoes" "text",
    "medicoes_ids" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone,
    "medicao_id" "uuid",
    "valor_glosa" numeric DEFAULT 0,
    "valor_aprovado" numeric,
    "validado_por" "text",
    "validado_em" timestamp with time zone,
    "encaminhado_em" timestamp with time zone,
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."portal_pedidos_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "unidade_id" bigint NOT NULL,
    "item_nome" "text" NOT NULL,
    "categoria" "text",
    "quantidade" integer DEFAULT 1 NOT NULL,
    "unidade_medida" "text" DEFAULT 'UNIDADE'::"text" NOT NULL,
    "especificacao" "text",
    "justificativa" "text",
    "prioridade" "text" DEFAULT 'NORMAL'::"text" NOT NULL,
    "status" "text" DEFAULT 'ATIVO'::"text" NOT NULL,
    "criado_por" "uuid",
    "atualizado_por" "uuid",
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "atualizado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "cancelado_em" timestamp with time zone,
    "atendido_em" timestamp with time zone,
    "sala_id" "uuid",
    "client_request_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    CONSTRAINT "portal_pedidos_itens_item_nome_check" CHECK ((("length"(TRIM(BOTH FROM "item_nome")) >= 2) AND ("length"(TRIM(BOTH FROM "item_nome")) <= 180))),
    CONSTRAINT "portal_pedidos_itens_prioridade_check" CHECK (("prioridade" = ANY (ARRAY['BAIXA'::"text", 'NORMAL'::"text", 'ALTA'::"text", 'URGENTE'::"text"]))),
    CONSTRAINT "portal_pedidos_itens_quantidade_check" CHECK (("quantidade" > 0)),
    CONSTRAINT "portal_pedidos_itens_status_check" CHECK (("status" = ANY (ARRAY['ATIVO'::"text", 'CANCELADO'::"text", 'ATENDIDO'::"text"]))),
    CONSTRAINT "portal_pedidos_itens_unidade_medida_check" CHECK (("unidade_medida" = ANY (ARRAY['UNIDADE'::"text", 'CAIXA'::"text", 'PACOTE'::"text", 'KIT'::"text", 'LITRO'::"text", 'METRO'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."licitacao_item_ocorrencias" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "item_id" "uuid" NOT NULL,
    "processo_id" bigint NOT NULL,
    "tipo" "text" NOT NULL,
    "numero_pregao" "text" NOT NULL,
    "numero_lote" "text" NOT NULL,
    "data_ocorrencia" "date" DEFAULT CURRENT_DATE NOT NULL,
    "observacao" "text",
    "documento_path" "text" NOT NULL,
    "documento_nome" "text" NOT NULL,
    "documento_mime" "text" NOT NULL,
    "documento_tamanho" bigint NOT NULL,
    "processo_identificador_snapshot" "text" NOT NULL,
    "item_descricao_snapshot" "text" NOT NULL,
    "quantidade_snapshot" numeric NOT NULL,
    "valor_unitario_snapshot" numeric NOT NULL,
    "valor_total_snapshot" numeric GENERATED ALWAYS AS ("round"(("quantidade_snapshot" * "valor_unitario_snapshot"), 2)) STORED,
    "secao_id" bigint NOT NULL,
    "criado_por" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "licitacao_item_ocorrencias_documento_mime_check" CHECK (("documento_mime" = ANY (ARRAY['application/pdf'::"text", 'image/jpeg'::"text", 'image/png'::"text", 'image/webp'::"text"]))),
    CONSTRAINT "licitacao_item_ocorrencias_documento_nome_preenchido" CHECK ((("char_length"("btrim"("documento_nome")) >= 1) AND ("char_length"("btrim"("documento_nome")) <= 255))),
    CONSTRAINT "licitacao_item_ocorrencias_documento_path_preenchido" CHECK ((("char_length"("btrim"("documento_path")) >= 1) AND ("char_length"("btrim"("documento_path")) <= 1000))),
    CONSTRAINT "licitacao_item_ocorrencias_documento_tamanho_check" CHECK ((("documento_tamanho" >= 1) AND ("documento_tamanho" <= 10485760))),
    CONSTRAINT "licitacao_item_ocorrencias_lote_preenchido" CHECK ((("char_length"("btrim"("numero_lote")) >= 1) AND ("char_length"("btrim"("numero_lote")) <= 100))),
    CONSTRAINT "licitacao_item_ocorrencias_pregao_preenchido" CHECK ((("char_length"("btrim"("numero_pregao")) >= 1) AND ("char_length"("btrim"("numero_pregao")) <= 100))),
    CONSTRAINT "licitacao_item_ocorrencias_quantidade_check" CHECK (("quantidade_snapshot" >= (0)::numeric)),
    CONSTRAINT "licitacao_item_ocorrencias_tipo_check" CHECK (("tipo" = ANY (ARRAY['FRACASSADO'::"text", 'DESERTO'::"text"]))),
    CONSTRAINT "licitacao_item_ocorrencias_valor_check" CHECK (("valor_unitario_snapshot" >= (0)::numeric))
);

CREATE TABLE IF NOT EXISTS "sueq"."inventario_movimentacoes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "inventario_unidade_id" "uuid" NOT NULL,
    "secao_id" bigint,
    "tipo" "text" NOT NULL,
    "data_movimentacao" "date" NOT NULL,
    "unidade_origem_id" bigint,
    "unidade_origem_nome" "text",
    "unidade_destino_id" bigint,
    "unidade_destino_nome" "text",
    "destinatario" "text",
    "previsao_devolucao" "date",
    "responsavel_entrega" "text",
    "responsavel_recebimento" "text",
    "motivo" "text",
    "observacao" "text",
    "documento_path" "text" NOT NULL,
    "documento_nome" "text" NOT NULL,
    "documento_mime" "text",
    "criado_por" "uuid" NOT NULL,
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "inventario_movimentacoes_tipo_check" CHECK (("tipo" = ANY (ARRAY['TRANSFERENCIA'::"text", 'EMPRESTIMO'::"text", 'DEVOLUCAO'::"text", 'BAIXA'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_execucao_reajustes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "ata_reajuste_id" "uuid" NOT NULL,
    "ata_execucao_id" "uuid" NOT NULL,
    "origem_recurso" "text" NOT NULL,
    "emenda_id" "uuid",
    "emenda_item_id" "uuid",
    "quantidade_reajustada" numeric(18,4) NOT NULL,
    "valor_unitario_anterior" numeric(18,4) NOT NULL,
    "valor_unitario_reajustado" numeric(18,4) NOT NULL,
    "valor_reajuste_unitario" numeric(18,4) NOT NULL,
    "valor_reajuste_total" numeric(18,2) NOT NULL,
    "empenho" "text" NOT NULL,
    "nota_fiscal" "text" NOT NULL,
    "status" "text" DEFAULT 'ATIVO'::"text" NOT NULL,
    "criado_por" "uuid" DEFAULT NULL,
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "cancelado_por" "uuid",
    "cancelado_em" timestamp with time zone,
    "secao_id" bigint,
    "empenho_id" "uuid" NOT NULL,
    CONSTRAINT "atas_execucao_reajustes_documentos_obrigatorios" CHECK (((NULLIF(TRIM(BOTH FROM "empenho"), ''::"text") IS NOT NULL) AND (NULLIF(TRIM(BOTH FROM "nota_fiscal"), ''::"text") IS NOT NULL))),
    CONSTRAINT "atas_execucao_reajustes_emenda_coerente" CHECK (((("origem_recurso" = 'emenda'::"text") AND ("emenda_id" IS NOT NULL) AND ("emenda_item_id" IS NOT NULL)) OR (("origem_recurso" = 'recurso_proprio'::"text") AND ("emenda_id" IS NULL) AND ("emenda_item_id" IS NULL)))),
    CONSTRAINT "atas_execucao_reajustes_origem_recurso_check" CHECK (("origem_recurso" = ANY (ARRAY['emenda'::"text", 'recurso_proprio'::"text"]))),
    CONSTRAINT "atas_execucao_reajustes_status_check" CHECK (("status" = ANY (ARRAY['ATIVO'::"text", 'CANCELADO'::"text"]))),
    CONSTRAINT "atas_execucao_reajustes_valores_validos" CHECK ((("quantidade_reajustada" > (0)::numeric) AND ("valor_unitario_anterior" >= (0)::numeric) AND ("valor_unitario_reajustado" > "valor_unitario_anterior") AND ("valor_reajuste_unitario" > (0)::numeric) AND ("valor_reajuste_total" > (0)::numeric)))
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_item_reajustes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "ata_item_id" "uuid" NOT NULL,
    "contrato_id" integer NOT NULL,
    "data_vigencia" "date" NOT NULL,
    "percentual" numeric(12,6) NOT NULL,
    "valor_unitario_anterior" numeric(18,4) NOT NULL,
    "valor_unitario_novo" numeric(18,4) NOT NULL,
    "observacoes" "text",
    "status" "text" DEFAULT 'ATIVO'::"text" NOT NULL,
    "criado_por" "uuid" DEFAULT NULL,
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "cancelado_por" "uuid",
    "cancelado_em" timestamp with time zone,
    "secao_id" bigint,
    CONSTRAINT "atas_item_reajustes_status_check" CHECK (("status" = ANY (ARRAY['ATIVO'::"text", 'CANCELADO'::"text"]))),
    CONSTRAINT "atas_item_reajustes_valores_validos" CHECK ((("valor_unitario_anterior" >= (0)::numeric) AND ("valor_unitario_novo" > (0)::numeric)))
);

CREATE TABLE IF NOT EXISTS "sueq"."ata_planejamento_emendas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "processo_id" bigint NOT NULL,
    "processo_item_id" "uuid" NOT NULL,
    "emenda_id" "uuid" NOT NULL,
    "emenda_item_id" "uuid" NOT NULL,
    "secao_id" bigint,
    "quantidade_prevista" numeric NOT NULL,
    "contrato_id" integer,
    "ata_item_id" "uuid",
    "ata_execucao_id" "uuid",
    "quantidade_requisitada" numeric,
    "status" "text" DEFAULT 'PLANEJAMENTO'::"text" NOT NULL,
    "observacoes" "text",
    "criado_por" "uuid" DEFAULT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "ata_planejamento_emendas_estado_check" CHECK (((("status" = 'PLANEJAMENTO'::"text") AND ("contrato_id" IS NULL) AND ("ata_item_id" IS NULL) AND ("ata_execucao_id" IS NULL) AND ("quantidade_requisitada" IS NULL)) OR (("status" = 'ATA_VIGENTE_AGUARDANDO_REQUISICAO'::"text") AND ("contrato_id" IS NOT NULL) AND ("ata_item_id" IS NOT NULL) AND ("ata_execucao_id" IS NULL) AND ("quantidade_requisitada" IS NULL)) OR (("status" = 'REQUISITADO'::"text") AND ("contrato_id" IS NOT NULL) AND ("ata_item_id" IS NOT NULL) AND ("ata_execucao_id" IS NOT NULL) AND ("quantidade_requisitada" IS NOT NULL)) OR ("status" = 'CANCELADO'::"text"))),
    CONSTRAINT "ata_planejamento_emendas_quantidade_prevista_check" CHECK (("quantidade_prevista" > (0)::numeric)),
    CONSTRAINT "ata_planejamento_emendas_quantidade_requisitada_check" CHECK ((("quantidade_requisitada" IS NULL) OR ("quantidade_requisitada" > (0)::numeric))),
    CONSTRAINT "ata_planejamento_emendas_status_check" CHECK (("status" = ANY (ARRAY['PLANEJAMENTO'::"text", 'ATA_VIGENTE_AGUARDANDO_REQUISICAO'::"text", 'REQUISITADO'::"text", 'CANCELADO'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_execucao" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "ata_item_id" "uuid",
    "emenda_id" "uuid",
    "emenda_item_id" "uuid",
    "cpl" "text",
    "sim" "text",
    "item" "text",
    "unidade" "text",
    "qtde" numeric,
    "valor" numeric,
    "empenho" "text",
    "data_af" "text",
    "af_numero" "text",
    "prev_entrega" "text",
    "dt_entrega" "text",
    "nf" "text",
    "obs_prazo" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "origem_recurso" "text",
    "data_entrega_unidade" "date",
    "termo_arquivo" "text",
    "termo_responsavel" "text",
    "termo_cargo" "text",
    "confirmacao_obs" "text",
    "secao_id" bigint,
    "possui_patrimonio" boolean,
    "controle_obs" "text",
    "codigo_siam_secretaria" "text",
    "email_solicitante" "text",
    "marca_modelo" "text",
    "tipo_material" "text",
    CONSTRAINT "atas_execucao_codigo_siam_secretaria_check" CHECK ((("codigo_siam_secretaria" IS NULL) OR ("origem_recurso" = 'carona'::"text"))),
    CONSTRAINT "atas_execucao_email_solicitante_check" CHECK ((("email_solicitante" IS NULL) OR (("origem_recurso" = 'carona'::"text") AND (("length"("btrim"("email_solicitante")) >= 3) AND ("length"("btrim"("email_solicitante")) <= 254)) AND ("btrim"("email_solicitante") ~~ '%_@_%._%'::"text")))),
    CONSTRAINT "atas_execucao_origem_recurso_check" CHECK ((("origem_recurso" IS NULL) OR ("origem_recurso" = ANY (ARRAY['emenda'::"text", 'recurso_proprio'::"text", 'carona'::"text"])))),
    CONSTRAINT "atas_execucao_tipo_material_check" CHECK ((("tipo_material" IS NULL) OR ("tipo_material" = ANY (ARRAY['PERMANENTE'::"text", 'CONSUMO'::"text"]))))
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_execucao_unidades" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "exec_id" "uuid" NOT NULL,
    "ata_item_id" "uuid",
    "emenda_item_id" "uuid",
    "unidade_seq" integer,
    "patrimonio" "text",
    "numero_serie" "text",
    "nota_fiscal_id" "uuid",
    "recebido_em" "date",
    "recebido_por" "text",
    "obs" "text",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "secao_id" bigint,
    "unidade_id" bigint,
    "unidade_nome" "text",
    "data_entrega_unidade" "date"
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_item_marca_apostilamentos" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "ata_item_id" "uuid" NOT NULL,
    "contrato_id" integer NOT NULL,
    "marca_modelo_anterior" "text",
    "marca_modelo_nova" "text" NOT NULL,
    "apostilamento" "text" NOT NULL,
    "data_apostilamento" "date" NOT NULL,
    "observacoes" "text",
    "execucoes_atualizadas" integer DEFAULT 0 NOT NULL,
    "criado_por" "uuid" DEFAULT NULL,
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "secao_id" bigint,
    "execucao_ids" "uuid"[] DEFAULT '{}'::"uuid"[] NOT NULL,
    CONSTRAINT "atas_item_marca_apostilamentos_execucoes_atualizadas_check" CHECK (("execucoes_atualizadas" >= 0))
);

CREATE TABLE IF NOT EXISTS "sueq"."atas_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer NOT NULL,
    "cpl" "text",
    "sim" "text",
    "item" "text",
    "marca_modelo" "text",
    "qtde_contratada" numeric,
    "valor_unit" numeric,
    "vencimento" "text",
    "status_contrato" "text" DEFAULT 'VIGENTE'::"text",
    "empresa" "text",
    "prazo_entrega" integer,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint,
    "data_encerramento" "date",
    "motivo_encerramento" "text",
    "saldo_reiniciado_em" "date",
    "codigo_siam" "text",
    "unidade_medida" "text",
    "renovacao_em_tramite" boolean DEFAULT false NOT NULL,
    "renovacao_em_tramite_em" timestamp with time zone,
    "encerramento_planejado" boolean DEFAULT false NOT NULL,
    "encerramento_planejado_em" timestamp with time zone,
    "categoria_id" bigint,
    CONSTRAINT "atas_itens_codigo_siam_formato_check" CHECK ((("codigo_siam" IS NULL) OR ((("char_length"("btrim"("codigo_siam")) >= 1) AND ("char_length"("btrim"("codigo_siam")) <= 50)) AND ("btrim"("codigo_siam") ~ '^[0-9.-]+$'::"text")))),
    CONSTRAINT "atas_itens_decisao_vigencia_exclusiva_check" CHECK ((NOT ("renovacao_em_tramite" AND "encerramento_planejado"))),
    CONSTRAINT "atas_itens_encerramento_planejado_consistente_check" CHECK (("encerramento_planejado" = ("encerramento_planejado_em" IS NOT NULL))),
    CONSTRAINT "atas_itens_renovacao_em_tramite_consistente_check" CHECK (("renovacao_em_tramite" = ("renovacao_em_tramite_em" IS NOT NULL))),
    CONSTRAINT "atas_itens_unidade_medida_formato_check" CHECK ((("unidade_medida" IS NULL) OR (("unidade_medida" = "btrim"("unidade_medida")) AND (("char_length"("unidade_medida") >= 1) AND ("char_length"("unidade_medida") <= 80)))))
);

CREATE TABLE IF NOT EXISTS "sueq"."categorias_licitacao" (
    "id" bigint NOT NULL,
    "nome" "text" NOT NULL,
    "nome_chave" "text" GENERATED ALWAYS AS ("upper"("regexp_replace"("translate"("btrim"("nome"), 'ÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇáàâãäéèêëíìîïóòôõöúùûüç'::"text", 'AAAAAEEEEIIIIOOOOOUUUUCaaaaaeeeeiiiiooooouuuuc'::"text"), '[[:space:]]+'::"text", ' '::"text", 'g'::"text"))) STORED,
    "ordem" integer DEFAULT 0 NOT NULL,
    "ativo" boolean DEFAULT true NOT NULL,
    "revisado" boolean DEFAULT false NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "categorias_licitacao_nome_check" CHECK ((("length"("btrim"("nome")) >= 2) AND ("length"("btrim"("nome")) <= 120)))
);

CREATE TABLE IF NOT EXISTS "sueq"."chamados" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "protocolo" "text",
    "carimbo" "text",
    "data_solicitacao" "text",
    "unidade" "text",
    "unidade_id" bigint,
    "equipamento" "text",
    "fabricante" "text",
    "serie" "text",
    "patrimonio" "text",
    "categoria" "text",
    "servico" "text",
    "problema" "text",
    "descricao" "text",
    "rechamado" "text",
    "data_rechamado" "text",
    "observacao" "text",
    "endereco" "text",
    "telefone" "text",
    "responsavel" "text",
    "grau_urgencia" "text",
    "email_retorno" "text",
    "status" "text" DEFAULT 'sem_status'::"text",
    "cpl_contrato" "text",
    "contrato_id" integer,
    "os_numero" "text",
    "servico_realizado" "text",
    "situacao_os" "text",
    "ocorrencias" "text",
    "glosa" numeric(10,2),
    "nf_referencia" "text",
    "competencia" "text",
    "fiscalizado_por" "text",
    "fiscalizado_em" "date",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint,
    "request_id" "uuid"
);

CREATE TABLE IF NOT EXISTS "sueq"."chamados_anexos" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "chamado_id" "uuid",
    "storage_path" "text" NOT NULL,
    "nome_original" "text",
    "tamanho_bytes" integer,
    "mime_type" "text",
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "apagado_em" timestamp with time zone,
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."chamados_controle" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "chamado_id" "uuid",
    "protocolo" "text",
    "chamado_protocolo" "text",
    "status" "text" DEFAULT 'Aberto'::"text",
    "data_atendimento" "text",
    "data_atendimento_os" "date",
    "empresa" "text",
    "os" "text",
    "feito" "text",
    "obs" "text",
    "motivo_invalido" "text",
    "cpl_contrato" "text",
    "contrato_id" integer,
    "servico_realizado" "text",
    "situacao_os" "text",
    "ocorrencias" "text",
    "glosa" numeric(10,2),
    "nf_referencia" "text",
    "competencia" "text",
    "fiscalizado_por" "text",
    "fiscalizado_em" "date",
    "updated_at" timestamp without time zone DEFAULT "now"(),
    "medicao_id" "uuid",
    "nota_fiscal_id" "uuid",
    "termo_ateste_id" "uuid",
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos" (
    "id" integer NOT NULL,
    "secao" "text",
    "prestador" "text",
    "cpl" "text",
    "objeto" "text",
    "numero_contrato" "text",
    "cnpj" "text",
    "cnpj_fornecedor" "text",
    "data_inicio" "date",
    "data_assinatura" "date",
    "vigencia_atual" "text",
    "vencimento" "text",
    "status" "text" DEFAULT 'VIGENTE'::"text",
    "fonte" "text",
    "valor_inicial" "text",
    "valor_atual" "text",
    "valor_mensal" "text",
    "valor_total" "text",
    "valor_inicial_num" numeric,
    "valor_atual_num" numeric,
    "valor_mensal_num" numeric,
    "valor_total_num" numeric,
    "aditivo" "text",
    "reajuste" "text",
    "fiscalizacao" "text",
    "obs" "text",
    "supressao" "text",
    "contato" "text",
    "empenhos" "text",
    "data_atualizacao" "text",
    "atualizado_em" "text",
    "total_periodos_vigencia" integer DEFAULT 1,
    "email_empresa" "text",
    "prefixo_chamado" "text",
    "fornecedor_id" bigint,
    "tipo_instrumento" "text" DEFAULT 'CONTRATO'::"text" NOT NULL,
    "processo_id" bigint,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint,
    "periodicidade_pagamento" "text",
    "valor_periodico_num" numeric,
    "modelo_execucao" "text",
    "data_base_reajuste" "date",
    "categoria_id" bigint,
    CONSTRAINT "contratos_periodicidade_pagamento_check" CHECK ((("periodicidade_pagamento" IS NULL) OR ("periodicidade_pagamento" = ANY (ARRAY['MENSAL'::"text", 'TRIMESTRAL'::"text"])))),
    CONSTRAINT "contratos_tipo_instrumento_check" CHECK (("tipo_instrumento" = ANY (ARRAY['CONTRATO'::"text", 'ATA'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_fiscalizadores" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "cpl" "text",
    "nome" "text",
    "cargo" "text",
    "data_inicio" "date",
    "data_fim" "date",
    "ativo" boolean DEFAULT true,
    "obs" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_historico" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "cpl" "text",
    "tipo" "text",
    "data_evento" "date",
    "percentual" "text",
    "valor_novo" "text",
    "valor_mensal_novo" "text",
    "vigencia_nova_inicio" "date",
    "vigencia_nova_fim" "date",
    "obs" "text",
    "fiscalizacao_nova" "text",
    "usuario" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "titulo" "text",
    "action_type" "text",
    "status_evento" "text",
    "valor_impacto" numeric,
    "valor_reajustado" numeric,
    "related_entity_type" "text",
    "related_entity_id" "text",
    "documento_id" "text",
    "secao_id" bigint,
    "periodicidade_calculo" "text",
    "periodos_considerados" integer,
    "quantidade_alterada" numeric,
    "valor_unitario_periodo" numeric,
    CONSTRAINT "contratos_historico_periodicidade_calculo_check" CHECK ((("periodicidade_calculo" IS NULL) OR ("periodicidade_calculo" = ANY (ARRAY['MENSAL'::"text", 'TRIMESTRAL'::"text"]))))
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_medicao_glosas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "medicao_id" "uuid" NOT NULL,
    "contrato_id" integer NOT NULL,
    "item_id" "uuid",
    "motivo" "text" NOT NULL,
    "periodo_afetado" "text",
    "quantidade_afetada" numeric,
    "valor_glosa" numeric DEFAULT 0 NOT NULL,
    "justificativa" "text",
    "status" "text" DEFAULT 'registrada'::"text" NOT NULL,
    "documento_url" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint,
    CONSTRAINT "contratos_medicao_glosas_status_check" CHECK (("status" = ANY (ARRAY['registrada'::"text", 'validada'::"text", 'cancelada'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_medicao_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "medicao_id" "uuid" NOT NULL,
    "contrato_id" integer NOT NULL,
    "item_id" "uuid",
    "descricao" "text",
    "unidade" "text",
    "quantidade_executada" numeric,
    "quantidade_aceita" numeric,
    "quantidade_recusada" numeric,
    "valor_unitario" numeric,
    "valor_total" numeric,
    "observacoes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_medicoes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer NOT NULL,
    "competencia" "text" NOT NULL,
    "tipo_medicao" "text" DEFAULT 'competencia'::"text" NOT NULL,
    "data_medicao" "date" DEFAULT CURRENT_DATE NOT NULL,
    "fiscal_responsavel" "text",
    "status" "text" DEFAULT 'rascunho'::"text" NOT NULL,
    "valor_bruto" numeric DEFAULT 0 NOT NULL,
    "valor_glosa" numeric DEFAULT 0 NOT NULL,
    "valor_liquido" numeric DEFAULT 0 NOT NULL,
    "observacoes" "text",
    "validado_por" "text",
    "validado_em" timestamp with time zone,
    "encaminhado_em" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone,
    "secao_id" bigint,
    "ciclo_numero" integer,
    "ciclo_inicio" "date",
    "ciclo_fim" "date",
    "data_execucao_preventiva" "date",
    "relatorio_servico_referencia" "text",
    CONSTRAINT "contratos_medicoes_ciclo_check" CHECK (((("ciclo_numero" IS NULL) OR ("ciclo_numero" > 0)) AND (("ciclo_inicio" IS NULL) OR ("ciclo_fim" IS NULL) OR ("ciclo_fim" >= "ciclo_inicio")))),
    CONSTRAINT "contratos_medicoes_status_check" CHECK (("status" = ANY (ARRAY['rascunho'::"text", 'registrada'::"text", 'aprovada_pelo_fiscal'::"text", 'aprovada_com_glosa'::"text", 'recusada'::"text", 'cancelada'::"text"]))),
    CONSTRAINT "contratos_medicoes_valores_check" CHECK ((("valor_bruto" >= (0)::numeric) AND ("valor_glosa" >= (0)::numeric) AND ("valor_liquido" >= (0)::numeric) AND ("valor_liquido" <= "valor_bruto")))
);

CREATE TABLE IF NOT EXISTS "sueq"."contratos_vigencias" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "cpl" "text",
    "numero" integer,
    "data_inicio" "date",
    "data_fim" "date",
    "texto_original" "text",
    "valor_total" numeric,
    "valor_mensal" numeric,
    "obs" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint,
    "periodicidade_pagamento" "text",
    "valor_periodico" numeric,
    CONSTRAINT "contratos_vigencias_periodicidade_pagamento_check" CHECK ((("periodicidade_pagamento" IS NULL) OR ("periodicidade_pagamento" = ANY (ARRAY['MENSAL'::"text", 'TRIMESTRAL'::"text"]))))
);

CREATE TABLE IF NOT EXISTS "sueq"."divisoes" (
    "id" bigint NOT NULL,
    "sigla" "text" NOT NULL,
    "ativo" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);

CREATE TABLE IF NOT EXISTS "sueq"."emenda_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "emenda_id" "uuid",
    "emenda" "text",
    "item" "text",
    "qtde" numeric,
    "vl_unitario" numeric,
    "vl_total" numeric,
    "cpl" "text",
    "processo_id" bigint,
    "status" "text",
    "status_id" bigint,
    "nota_fiscal" "text",
    "empenho" "text",
    "patrimonio" "text",
    "unidade_beneficiada" "text",
    "unidade_beneficiada_id" bigint,
    "unidade_entrega" "text",
    "unidade_entrega_id" bigint,
    "data_entrega" "text",
    "ordem_pagamento" "text",
    "item_cadastrado" "text",
    "qtde_cadastrada" numeric,
    "vl_unitario_cadastrado" numeric,
    "vl_total_cadastrado" numeric,
    "data_atualizacao" "text",
    "comprovante_pagamento" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."emendas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "tipo" "text",
    "emenda" "text",
    "numero" "text",
    "parlamentar" "text",
    "sei_emenda" "text",
    "sei" "text",
    "valor_cedido" numeric,
    "unidade" "text",
    "ano" integer,
    "unidade_id" bigint,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "objeto" "text",
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."empenho_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "empenho_id" "uuid" NOT NULL,
    "item_id" "uuid",
    "emenda_id" "uuid",
    "emenda_item_id" "uuid",
    "quantidade_vinculada" numeric,
    "valor_vinculado" numeric,
    "exec_id" "uuid",
    "observacoes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."empenhos" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "numero" "text" NOT NULL,
    "numero_normalizado" "text",
    "ano" integer,
    "processo_id" bigint,
    "contrato_id" integer,
    "fornecedor_id" bigint,
    "emenda_id" "uuid",
    "fonte_tipo" "text",
    "fonte_descricao" "text",
    "valor_empenhado" numeric,
    "valor_anulado" numeric DEFAULT 0,
    "saldo_empenho" numeric,
    "data_emissao" "date",
    "numero_despesa" "text",
    "status" "text" DEFAULT 'emitido'::"text",
    "origem_sistema" "text",
    "origem_codigo" "text",
    "ultima_sincronizacao" timestamp with time zone,
    "raw_data" "jsonb",
    "arquivo_url" "text",
    "observacoes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone,
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."entregas_observacoes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "item_id" "uuid",
    "item_entrega_id" "uuid",
    "ata_execucao_id" "uuid",
    "secao_id" bigint NOT NULL,
    "texto" "text" NOT NULL,
    "autor_id" "uuid",
    "autor_nome" "text" NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_by" "uuid",
    "updated_by_nome" "text",
    "updated_at" timestamp with time zone,
    "migrada" boolean DEFAULT false NOT NULL,
    CONSTRAINT "entregas_observacoes_origem_check" CHECK (("num_nonnulls"("item_id", "item_entrega_id", "ata_execucao_id") = 1)),
    CONSTRAINT "entregas_observacoes_texto_check" CHECK (("btrim"("texto") <> ''::"text"))
);

CREATE TABLE IF NOT EXISTS "sueq"."entregas_prazos_historico" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "item_entrega_id" "uuid",
    "ata_execucao_id" "uuid",
    "prazo_anterior" "date" NOT NULL,
    "prazo_novo" "date" NOT NULL,
    "observacao" "text",
    "alterado_por" "uuid" DEFAULT NULL,
    "alterado_em" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "entregas_prazos_historico_datas_check" CHECK (("prazo_anterior" <> "prazo_novo")),
    CONSTRAINT "entregas_prazos_historico_origem_check" CHECK (((("item_entrega_id" IS NOT NULL) AND ("ata_execucao_id" IS NULL)) OR (("item_entrega_id" IS NULL) AND ("ata_execucao_id" IS NOT NULL))))
);

CREATE TABLE IF NOT EXISTS "sueq"."fiscalizacao_historico" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "chamado_id" "uuid",
    "contrato_id" integer,
    "protocolo" "text",
    "status" "text",
    "observacao" "text",
    "usuario" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint,
    "situacao_anterior" "text",
    "situacao_nova" "text",
    "data_alteracao" "date",
    "alterado_por" "text"
);

CREATE TABLE IF NOT EXISTS "sueq"."fornecedor_contatos" (
    "id" bigint NOT NULL,
    "fornecedor_id" bigint,
    "nome" "text",
    "cargo" "text",
    "email" "text",
    "telefone" "text",
    "principal" boolean DEFAULT false,
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."fornecedores" (
    "id" bigint NOT NULL,
    "cnpj_normalizado" "text",
    "razao_social" "text",
    "nome_fantasia" "text",
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."inventario_ac" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "num" "text",
    "unidade" "text",
    "equipamento" "text",
    "patrimonio" "text",
    "serie" "text",
    "modelo" "text",
    "fabricante" "text",
    "status" "text",
    "observacao" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."inventario_unidades" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "origem_tipo" "text" NOT NULL,
    "unidade_fisica_id" "uuid" NOT NULL,
    "secao_id" bigint,
    "unidade_origem_id" bigint,
    "unidade_origem_nome" "text",
    "unidade_atual_id" bigint,
    "unidade_atual_nome" "text",
    "situacao_atual" "text" DEFAULT 'ATIVO'::"text" NOT NULL,
    "responsavel_atual" "text",
    "emprestado_para" "text",
    "previsao_devolucao" "date",
    "ultima_movimentacao_em" timestamp with time zone,
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "atualizado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "inventario_unidades_origem_tipo_check" CHECK (("origem_tipo" = ANY (ARRAY['AQUISICAO'::"text", 'ATA'::"text"]))),
    CONSTRAINT "inventario_unidades_situacao_atual_check" CHECK (("situacao_atual" = ANY (ARRAY['ATIVO'::"text", 'EMPRESTADO'::"text", 'BAIXADO'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "processo_id" bigint,
    "origem" "text" DEFAULT 'aquisicao'::"text" NOT NULL,
    "fonte_tipo" "text",
    "emenda_id" "uuid",
    "emenda_item_id" "uuid",
    "fonte_descricao" "text",
    "grupo_item_id" "uuid",
    "descricao" "text",
    "qtde" numeric,
    "valor_estimado" numeric,
    "prazo_entrega_dias" integer,
    "unidade_destino_id" bigint,
    "contrato_id" integer,
    "fornecedor_id" bigint,
    "valor_contratado" numeric,
    "ata_item_id" "uuid",
    "status" "text" DEFAULT 'em licitacao'::"text",
    "status_lic_id" bigint,
    "status_lic_desde" timestamp with time zone,
    "marca" "text",
    "modelo" "text",
    "observacoes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint,
    "controle_obs" "text",
    "status_lic_secretaria_id" bigint,
    "status_lic_texto" character varying(55),
    "codigo_siam" "text",
    "unidade_medida" "text",
    "categoria_id" bigint,
    CONSTRAINT "itens_codigo_siam_formato_check" CHECK ((("codigo_siam" IS NULL) OR ((("char_length"("btrim"("codigo_siam")) >= 1) AND ("char_length"("btrim"("codigo_siam")) <= 50)) AND ("btrim"("codigo_siam") ~ '^[0-9.-]+$'::"text")))),
    CONSTRAINT "itens_status_lic_situacao_preenchida" CHECK (((("status_lic_secretaria_id" IS NULL) AND ("status_lic_texto" IS NULL)) OR (("status_lic_secretaria_id" IS NOT NULL) AND (NULLIF("btrim"(("status_lic_texto")::"text"), ''::"text") IS NOT NULL)))),
    CONSTRAINT "itens_unidade_medida_formato_check" CHECK ((("unidade_medida" IS NULL) OR (("unidade_medida" = "btrim"("unidade_medida")) AND (("char_length"("unidade_medida") >= 1) AND ("char_length"("unidade_medida") <= 80)))))
);

CREATE TABLE IF NOT EXISTS "sueq"."itens_entregas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "item_id" "uuid" NOT NULL,
    "af_numero" "text",
    "af_data" "date",
    "qtde_autorizada" numeric,
    "data_limite_entrega" "date",
    "nota_fiscal" "text",
    "nota_fiscal_id" "uuid",
    "nf_data" "date",
    "empenho" "text",
    "empenho_id" "uuid",
    "patrimonio" "text",
    "numero_serie" "text",
    "qtde_recebida" numeric,
    "data_recebimento" "date",
    "recebido_por" "text",
    "recebimento_tipo" "text",
    "data_entrega_unidade" "date",
    "termo_arquivo" "text",
    "termo_responsavel" "text",
    "termo_cargo" "text",
    "confirmacao_obs" "text",
    "status" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "af_obs" "text",
    "secao_id" bigint,
    "possui_patrimonio" boolean,
    "controle_obs" "text",
    "tipo_material" "text",
    CONSTRAINT "itens_entregas_tipo_material_check" CHECK ((("tipo_material" IS NULL) OR ("tipo_material" = ANY (ARRAY['PERMANENTE'::"text", 'CONSUMO'::"text"]))))
);

CREATE TABLE IF NOT EXISTS "sueq"."itens_entregas_unidades" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "entrega_id" "uuid",
    "item_id" "uuid",
    "unidade_id" bigint,
    "unidade_nome" "text",
    "quantidade" numeric DEFAULT 1 NOT NULL,
    "patrimonio" "text",
    "numero_serie" "text",
    "nota_fiscal_id" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "unidade_seq" integer,
    "recebido_em" "date",
    "recebido_por" "text",
    "obs" "text",
    "secao_id" bigint,
    CONSTRAINT "itens_entregas_unidades_quantidade_unitaria" CHECK (("quantidade" = (1)::numeric))
);

CREATE TABLE IF NOT EXISTS "sueq"."itens_status_historico" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "item_id" "uuid",
    "status_id" bigint,
    "status_nome" "text",
    "mudado_por" "uuid",
    "origem" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."licitacao_item_ocorrencia_emendas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "ocorrencia_id" "uuid" NOT NULL,
    "emenda_id" "uuid" NOT NULL,
    "emenda_item_id" "uuid" NOT NULL,
    "quantidade_snapshot" numeric NOT NULL,
    "valor_unitario_snapshot" numeric NOT NULL,
    "valor_total_snapshot" numeric GENERATED ALWAYS AS ("round"(("quantidade_snapshot" * "valor_unitario_snapshot"), 2)) STORED,
    "secao_id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "licitacao_item_ocorrencia_emendas_quantidade_check" CHECK (("quantidade_snapshot" >= (0)::numeric)),
    CONSTRAINT "licitacao_item_ocorrencia_emendas_valor_check" CHECK (("valor_unitario_snapshot" >= (0)::numeric))
);

CREATE TABLE IF NOT EXISTS "sueq"."nf_checklist_documento_contratos" (
    "documento_id" "uuid" NOT NULL,
    "contrato_id" integer NOT NULL,
    "secao_id" bigint NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);

CREATE TABLE IF NOT EXISTS "sueq"."nf_checklist_documentos" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "secao_id" bigint NOT NULL,
    "nome" "text" NOT NULL,
    "descricao" "text",
    "ordem" integer DEFAULT 0 NOT NULL,
    "ativo" boolean DEFAULT true NOT NULL,
    "created_by" "uuid",
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "aplica_todos" boolean DEFAULT true NOT NULL,
    "contrato_id" integer,
    CONSTRAINT "nf_checklist_documentos_nome_check" CHECK (("length"("btrim"("nome")) > 0))
);

CREATE TABLE IF NOT EXISTS "sueq"."nf_checklist_marcacoes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "secao_id" bigint NOT NULL,
    "contrato_id" integer NOT NULL,
    "documento_id" "uuid" NOT NULL,
    "competencia" "date" NOT NULL,
    "concluido" boolean DEFAULT true NOT NULL,
    "observacoes" "text",
    "marcado_por" "uuid",
    "marcado_em" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "nf_checklist_marcacoes_competencia_check" CHECK (("competencia" = ("date_trunc"('month'::"text", ("competencia")::timestamp with time zone))::"date"))
);

CREATE TABLE IF NOT EXISTS "sueq"."nota_fiscal_itens" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "nota_fiscal_id" "uuid" NOT NULL,
    "item_id" "uuid",
    "emenda_id" "uuid",
    "emenda_item_id" "uuid",
    "empenho_id" "uuid",
    "quantidade" numeric,
    "valor_unitario" numeric,
    "valor_total" numeric,
    "observacoes" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint,
    "exec_id" "uuid"
);

CREATE TABLE IF NOT EXISTS "sueq"."parlamentares" (
    "id" bigint NOT NULL,
    "nome" "text",
    "partido" "text",
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."pessoas" (
    "id" bigint NOT NULL,
    "nome" "text",
    "cargo" "text",
    "orgao" "text",
    "email" "text",
    "telefone" "text",
    "usuario_id" "uuid",
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."portal_salas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "unidade_id" bigint NOT NULL,
    "nome" "text" NOT NULL,
    "descricao" "text",
    "ativo" boolean DEFAULT true NOT NULL,
    "criado_por" "uuid",
    "criado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "atualizado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "portal_salas_nome_check" CHECK ((("length"(TRIM(BOTH FROM "nome")) >= 2) AND ("length"(TRIM(BOTH FROM "nome")) <= 120)))
);

CREATE TABLE IF NOT EXISTS "sueq"."portal_unidades_acessos" (
    "user_id" "uuid" NOT NULL,
    "unidade_solicitada_id" bigint NOT NULL,
    "unidade_id" bigint,
    "status" "text" DEFAULT 'PENDENTE'::"text" NOT NULL,
    "solicitado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    "revisado_em" timestamp with time zone,
    "revisado_por" "uuid",
    "observacao_revisao" "text",
    CONSTRAINT "portal_acesso_aprovado_com_unidade" CHECK ((("status" <> 'APROVADO'::"text") OR ("unidade_id" IS NOT NULL))),
    CONSTRAINT "portal_unidades_acessos_status_check" CHECK (("status" = ANY (ARRAY['PENDENTE'::"text", 'APROVADO'::"text", 'REJEITADO'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."processos" (
    "id" bigint NOT NULL,
    "identificador" "text" NOT NULL,
    "tipo" "text",
    "natureza" "text",
    "objeto" "text",
    "modalidade" "text",
    "status" "text",
    "secao" "text",
    "valor_estimado" numeric,
    "observacao" "text",
    "gera_mais_contratos" boolean DEFAULT false NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "tipo_servico" "text",
    "servico_mensal_itens" "jsonb",
    "servico_mensal_meses" integer,
    "servico_mensal_valor_mensal" numeric,
    "servico_mensal_valor_global" numeric,
    "servico_demanda_meses" integer,
    "sc" "text",
    "secao_id" bigint,
    "servico_trimestral_itens" "jsonb",
    "servico_trimestral_meses" integer,
    "servico_trimestral_ciclos" integer,
    "servico_trimestral_valor_trimestral" numeric,
    "servico_trimestral_valor_global" numeric,
    "link_publico_sei" "text",
    "categoria_id" bigint,
    CONSTRAINT "processos_link_publico_sei_http_check" CHECK ((("link_publico_sei" IS NULL) OR ("btrim"("link_publico_sei") ~* '^https?://[^[:space:]]+$'::"text")))
);

CREATE TABLE IF NOT EXISTS "sueq"."profiles" (
    "id" "uuid" NOT NULL,
    "nome" "text",
    "email" "text",
    "papel" "text" DEFAULT 'visualizador'::"text" NOT NULL,
    "aprovado" boolean DEFAULT false NOT NULL,
    "created_at" timestamp without time zone DEFAULT "now"(),
    "escopo_organizacional" "text" DEFAULT 'secao'::"text" NOT NULL,
    "secao_id" bigint,
    "contexto_modo" "text" DEFAULT 'secao'::"text" NOT NULL,
    "contexto_secao_id" bigint,
    "divisao_id" bigint,
    "contexto_divisao_id" bigint,
    CONSTRAINT "profiles_contexto_modo_check" CHECK (("contexto_modo" = ANY (ARRAY['secao'::"text", 'divisao'::"text", 'global'::"text"]))),
    CONSTRAINT "profiles_escopo_organizacional_check" CHECK (("escopo_organizacional" = ANY (ARRAY['secao'::"text", 'divisao'::"text"])))
);

CREATE TABLE IF NOT EXISTS "sueq"."sancao_itens" (
    "id" bigint NOT NULL,
    "sancao_id" "uuid",
    "ref_origem" "text",
    "descricao" "text",
    "cpl" "text",
    "sim" "text",
    "unidade" "text",
    "qtde" numeric,
    "vl_unitario" numeric,
    "vl_total" numeric,
    "empenho" "text",
    "data_af" "text",
    "prev_entrega" "text",
    "dt_entrega" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."sancoes_administrativas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "tipo" "text",
    "status" "text",
    "valor" numeric,
    "data_evento" "date",
    "observacao" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."sancoes_solicitadas" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "protocolo" "text",
    "tipo" "text",
    "motivo" "text",
    "status" "text" DEFAULT 'solicitada'::"text",
    "observacao" "text",
    "payload" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."secoes" (
    "id" bigint NOT NULL,
    "sigla" "text",
    "nome" "text",
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "divisao_id" bigint NOT NULL
);

CREATE TABLE IF NOT EXISTS "sueq"."secretarias" (
    "id" bigint NOT NULL,
    "sigla" "text" NOT NULL,
    "nome" "text" NOT NULL,
    "ativo" boolean DEFAULT true NOT NULL,
    "revisado" boolean DEFAULT true NOT NULL,
    "created_at" timestamp with time zone DEFAULT "now"() NOT NULL
);

CREATE TABLE IF NOT EXISTS "sueq"."secretario_atual" (
    "id" smallint DEFAULT 1 NOT NULL,
    "nome" "text" NOT NULL,
    "cargo" "text",
    "secretaria" "text",
    "ato_nomeacao" "text",
    "email" "text",
    "telefone" "text",
    "atualizado_em" timestamp with time zone DEFAULT "now"() NOT NULL,
    CONSTRAINT "secretario_atual_registro_unico" CHECK (("id" = 1))
);

CREATE TABLE IF NOT EXISTS "sueq"."status_opcoes" (
    "id" bigint NOT NULL,
    "contexto" "text",
    "nome" "text" NOT NULL,
    "ordem" integer DEFAULT 0,
    "orgao" "text",
    "automatico" boolean DEFAULT false,
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."termo_chamados" (
    "id" bigint NOT NULL,
    "termo_id" "uuid",
    "chamado_id" "uuid",
    "protocolo" "text",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."termo_contratos" (
    "id" bigint NOT NULL,
    "termo_id" "uuid",
    "contrato_id" integer,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."termos_ateste" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "contrato_id" integer,
    "chamado_id" "uuid",
    "protocolo" "text",
    "arquivo_url" "text",
    "responsavel" "text",
    "cargo" "text",
    "observacao" "text",
    "created_at" timestamp without time zone DEFAULT "now"(),
    "medicao_id" "uuid",
    "nota_fiscal_id" "uuid",
    "protocolos" "jsonb" DEFAULT '[]'::"jsonb",
    "valor_atestado" numeric DEFAULT 0,
    "cpl_contrato" "text",
    "competencia" "text",
    "nf_referencia" "text",
    "fiscalizado_por" "text",
    "gerado_em" "date",
    "secao_id" bigint
);

CREATE TABLE IF NOT EXISTS "sueq"."unidades" (
    "id" bigint NOT NULL,
    "nome" "text",
    "nome_chave" "text",
    "endereco" "text",
    "telefone" "text",
    "ativo" boolean DEFAULT true,
    "revisado" boolean DEFAULT true,
    "created_at" timestamp with time zone DEFAULT "now"()
);

CREATE TABLE IF NOT EXISTS "sueq"."user_tab_permissions" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_id" "uuid" NOT NULL,
    "tab_key" "text" NOT NULL,
    "can_view" boolean DEFAULT true,
    "can_edit" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "now"()
);

ALTER TABLE "sueq"."categorias_licitacao" ALTER COLUMN "id" ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME "sueq"."categorias_licitacao_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."contratos" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."contratos_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."divisoes" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."divisoes_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."fornecedor_contatos" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."fornecedor_contatos_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."fornecedores" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."fornecedores_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."parlamentares" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."parlamentares_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."pessoas" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."pessoas_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."processos" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."processos_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."sancao_itens" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."sancao_itens_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."secoes" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."secoes_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."secretarias" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."secretarias_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."status_opcoes" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."status_opcoes_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."termo_chamados" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."termo_chamados_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."termo_contratos" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."termo_contratos_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE "sueq"."unidades" ALTER COLUMN "id" ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME "sueq"."unidades_id_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_execucao"
    ADD CONSTRAINT "atas_execucao_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_item_marca_apostilamentos"
    ADD CONSTRAINT "atas_item_marca_apostilamentos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_item_reajustes"
    ADD CONSTRAINT "atas_item_reajustes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."atas_itens"
    ADD CONSTRAINT "atas_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."categorias_licitacao"
    ADD CONSTRAINT "categorias_licitacao_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."chamados_anexos"
    ADD CONSTRAINT "chamados_anexos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_protocolo_key" UNIQUE ("protocolo");

ALTER TABLE ONLY "sueq"."chamados"
    ADD CONSTRAINT "chamados_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."chamados"
    ADD CONSTRAINT "chamados_protocolo_key" UNIQUE ("protocolo");

ALTER TABLE ONLY "sueq"."contratos_fiscalizadores"
    ADD CONSTRAINT "contratos_fiscalizadores_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos_historico"
    ADD CONSTRAINT "contratos_historico_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_glosas"
    ADD CONSTRAINT "contratos_medicao_glosas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_itens"
    ADD CONSTRAINT "contratos_medicao_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos_medicoes"
    ADD CONSTRAINT "contratos_medicoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos"
    ADD CONSTRAINT "contratos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."contratos_vigencias"
    ADD CONSTRAINT "contratos_vigencias_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."divisoes"
    ADD CONSTRAINT "divisoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."divisoes"
    ADD CONSTRAINT "divisoes_sigla_key" UNIQUE ("sigla");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."emendas"
    ADD CONSTRAINT "emendas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."entregas_prazos_historico"
    ADD CONSTRAINT "entregas_prazos_historico_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."fiscalizacao_historico"
    ADD CONSTRAINT "fiscalizacao_historico_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."fornecedor_contatos"
    ADD CONSTRAINT "fornecedor_contatos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."fornecedores"
    ADD CONSTRAINT "fornecedores_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."inventario_ac"
    ADD CONSTRAINT "inventario_ac_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."inventario_movimentacoes"
    ADD CONSTRAINT "inventario_movimentacoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."inventario_unidades"
    ADD CONSTRAINT "inventario_unidades_origem_tipo_unidade_fisica_id_key" UNIQUE ("origem_tipo", "unidade_fisica_id");

ALTER TABLE ONLY "sueq"."inventario_unidades"
    ADD CONSTRAINT "inventario_unidades_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."itens_entregas"
    ADD CONSTRAINT "itens_entregas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."itens_status_historico"
    ADD CONSTRAINT "itens_status_historico_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_unica" UNIQUE ("ocorrencia_id", "emenda_item_id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencias"
    ADD CONSTRAINT "licitacao_item_ocorrencias_item_unico" UNIQUE ("item_id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencias"
    ADD CONSTRAINT "licitacao_item_ocorrencias_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."nf_checklist_documento_contratos"
    ADD CONSTRAINT "nf_checklist_documento_contratos_pkey" PRIMARY KEY ("documento_id", "contrato_id");

ALTER TABLE ONLY "sueq"."nf_checklist_documentos"
    ADD CONSTRAINT "nf_checklist_documentos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."nf_checklist_marcacoes"
    ADD CONSTRAINT "nf_checklist_marcacoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."parlamentares"
    ADD CONSTRAINT "parlamentares_nome_key" UNIQUE ("nome");

ALTER TABLE ONLY "sueq"."parlamentares"
    ADD CONSTRAINT "parlamentares_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."pessoas"
    ADD CONSTRAINT "pessoas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."portal_inventario"
    ADD CONSTRAINT "portal_inventario_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."portal_pedidos_itens"
    ADD CONSTRAINT "portal_pedidos_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."portal_salas"
    ADD CONSTRAINT "portal_salas_id_unidade_id_key" UNIQUE ("id", "unidade_id");

ALTER TABLE ONLY "sueq"."portal_salas"
    ADD CONSTRAINT "portal_salas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_inventario_inventario_origem_id_key" UNIQUE ("inventario_origem_id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_inventario_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."portal_unidades_acessos"
    ADD CONSTRAINT "portal_unidades_acessos_pkey" PRIMARY KEY ("user_id");

ALTER TABLE ONLY "sueq"."processos"
    ADD CONSTRAINT "processos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."profiles"
    ADD CONSTRAINT "profiles_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."sancao_itens"
    ADD CONSTRAINT "sancao_itens_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."sancoes_administrativas"
    ADD CONSTRAINT "sancoes_administrativas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."sancoes_solicitadas"
    ADD CONSTRAINT "sancoes_solicitadas_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."secoes"
    ADD CONSTRAINT "secoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."secoes"
    ADD CONSTRAINT "secoes_sigla_key" UNIQUE ("sigla");

ALTER TABLE ONLY "sueq"."secretarias"
    ADD CONSTRAINT "secretarias_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."secretarias"
    ADD CONSTRAINT "secretarias_sigla_key" UNIQUE ("sigla");

ALTER TABLE ONLY "sueq"."secretario_atual"
    ADD CONSTRAINT "secretario_atual_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."status_opcoes"
    ADD CONSTRAINT "status_opcoes_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."termo_chamados"
    ADD CONSTRAINT "termo_chamados_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."termo_contratos"
    ADD CONSTRAINT "termo_contratos_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."unidades"
    ADD CONSTRAINT "unidades_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."nf_checklist_marcacoes"
    ADD CONSTRAINT "uq_nf_checklist_marcacao" UNIQUE ("contrato_id", "documento_id", "competencia");

ALTER TABLE ONLY "sueq"."user_tab_permissions"
    ADD CONSTRAINT "user_tab_permissions_pkey" PRIMARY KEY ("id");

ALTER TABLE ONLY "sueq"."user_tab_permissions"
    ADD CONSTRAINT "user_tab_permissions_user_id_tab_key_key" UNIQUE ("user_id", "tab_key");

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_ata_execucao_id_fkey" FOREIGN KEY ("ata_execucao_id") REFERENCES "sueq"."atas_execucao"("id");

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id");

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_processo_item_id_fkey" FOREIGN KEY ("processo_item_id") REFERENCES "sueq"."itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."ata_planejamento_emendas"
    ADD CONSTRAINT "ata_planejamento_emendas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_execucao"
    ADD CONSTRAINT "atas_execucao_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."atas_execucao"
    ADD CONSTRAINT "atas_execucao_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."atas_execucao"
    ADD CONSTRAINT "atas_execucao_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id");

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_ata_execucao_id_fkey" FOREIGN KEY ("ata_execucao_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_ata_reajuste_id_fkey" FOREIGN KEY ("ata_reajuste_id") REFERENCES "sueq"."atas_item_reajustes"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_empenho_id_fkey" FOREIGN KEY ("empenho_id") REFERENCES "sueq"."empenhos"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_execucao_reajustes"
    ADD CONSTRAINT "atas_execucao_reajustes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_execucao"
    ADD CONSTRAINT "atas_execucao_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id");

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_exec_id_fkey" FOREIGN KEY ("exec_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id");

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_execucao_unidades"
    ADD CONSTRAINT "atas_execucao_unidades_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."atas_item_marca_apostilamentos"
    ADD CONSTRAINT "atas_item_marca_apostilamentos_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_item_marca_apostilamentos"
    ADD CONSTRAINT "atas_item_marca_apostilamentos_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_item_marca_apostilamentos"
    ADD CONSTRAINT "atas_item_marca_apostilamentos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_item_reajustes"
    ADD CONSTRAINT "atas_item_reajustes_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_item_reajustes"
    ADD CONSTRAINT "atas_item_reajustes_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_item_reajustes"
    ADD CONSTRAINT "atas_item_reajustes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."atas_itens"
    ADD CONSTRAINT "atas_itens_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "sueq"."categorias_licitacao"("id") ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."atas_itens"
    ADD CONSTRAINT "atas_itens_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."atas_itens"
    ADD CONSTRAINT "atas_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."chamados_anexos"
    ADD CONSTRAINT "chamados_anexos_chamado_id_fkey" FOREIGN KEY ("chamado_id") REFERENCES "sueq"."chamados"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."chamados_anexos"
    ADD CONSTRAINT "chamados_anexos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."chamados"
    ADD CONSTRAINT "chamados_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_chamado_id_fkey" FOREIGN KEY ("chamado_id") REFERENCES "sueq"."chamados"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_medicao_id_fkey" FOREIGN KEY ("medicao_id") REFERENCES "sueq"."contratos_medicoes"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."chamados_controle"
    ADD CONSTRAINT "chamados_controle_termo_ateste_id_fkey" FOREIGN KEY ("termo_ateste_id") REFERENCES "sueq"."termos_ateste"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."chamados"
    ADD CONSTRAINT "chamados_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."chamados"
    ADD CONSTRAINT "chamados_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."contratos"
    ADD CONSTRAINT "contratos_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "sueq"."categorias_licitacao"("id") ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."contratos_fiscalizadores"
    ADD CONSTRAINT "contratos_fiscalizadores_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_fiscalizadores"
    ADD CONSTRAINT "contratos_fiscalizadores_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos"
    ADD CONSTRAINT "contratos_fornecedor_id_fkey" FOREIGN KEY ("fornecedor_id") REFERENCES "sueq"."fornecedores"("id");

ALTER TABLE ONLY "sueq"."contratos_historico"
    ADD CONSTRAINT "contratos_historico_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_historico"
    ADD CONSTRAINT "contratos_historico_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_glosas"
    ADD CONSTRAINT "contratos_medicao_glosas_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_medicao_glosas"
    ADD CONSTRAINT "contratos_medicao_glosas_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_glosas"
    ADD CONSTRAINT "contratos_medicao_glosas_medicao_id_fkey" FOREIGN KEY ("medicao_id") REFERENCES "sueq"."contratos_medicoes"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_medicao_glosas"
    ADD CONSTRAINT "contratos_medicao_glosas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_itens"
    ADD CONSTRAINT "contratos_medicao_itens_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_medicao_itens"
    ADD CONSTRAINT "contratos_medicao_itens_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id");

ALTER TABLE ONLY "sueq"."contratos_medicao_itens"
    ADD CONSTRAINT "contratos_medicao_itens_medicao_id_fkey" FOREIGN KEY ("medicao_id") REFERENCES "sueq"."contratos_medicoes"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_medicao_itens"
    ADD CONSTRAINT "contratos_medicao_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos_medicoes"
    ADD CONSTRAINT "contratos_medicoes_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_medicoes"
    ADD CONSTRAINT "contratos_medicoes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos"
    ADD CONSTRAINT "contratos_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id");

ALTER TABLE ONLY "sueq"."contratos"
    ADD CONSTRAINT "contratos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."contratos_vigencias"
    ADD CONSTRAINT "contratos_vigencias_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."contratos_vigencias"
    ADD CONSTRAINT "contratos_vigencias_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_status_id_fkey" FOREIGN KEY ("status_id") REFERENCES "sueq"."status_opcoes"("id");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_unidade_beneficiada_id_fkey" FOREIGN KEY ("unidade_beneficiada_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."emenda_itens"
    ADD CONSTRAINT "emenda_itens_unidade_entrega_id_fkey" FOREIGN KEY ("unidade_entrega_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."emendas"
    ADD CONSTRAINT "emendas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."emendas"
    ADD CONSTRAINT "emendas_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id");

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_empenho_id_fkey" FOREIGN KEY ("empenho_id") REFERENCES "sueq"."empenhos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_exec_id_fkey" FOREIGN KEY ("exec_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id");

ALTER TABLE ONLY "sueq"."empenho_itens"
    ADD CONSTRAINT "empenho_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_fornecedor_id_fkey" FOREIGN KEY ("fornecedor_id") REFERENCES "sueq"."fornecedores"("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id");

ALTER TABLE ONLY "sueq"."empenhos"
    ADD CONSTRAINT "empenhos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_ata_execucao_id_fkey" FOREIGN KEY ("ata_execucao_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_autor_id_fkey" FOREIGN KEY ("autor_id") REFERENCES "sueq"."profiles"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_item_entrega_id_fkey" FOREIGN KEY ("item_entrega_id") REFERENCES "sueq"."itens_entregas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."entregas_observacoes"
    ADD CONSTRAINT "entregas_observacoes_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "sueq"."profiles"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."entregas_prazos_historico"
    ADD CONSTRAINT "entregas_prazos_historico_ata_execucao_id_fkey" FOREIGN KEY ("ata_execucao_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."entregas_prazos_historico"
    ADD CONSTRAINT "entregas_prazos_historico_item_entrega_id_fkey" FOREIGN KEY ("item_entrega_id") REFERENCES "sueq"."itens_entregas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."fiscalizacao_historico"
    ADD CONSTRAINT "fiscalizacao_historico_chamado_id_fkey" FOREIGN KEY ("chamado_id") REFERENCES "sueq"."chamados"("id");

ALTER TABLE ONLY "sueq"."fiscalizacao_historico"
    ADD CONSTRAINT "fiscalizacao_historico_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."fiscalizacao_historico"
    ADD CONSTRAINT "fiscalizacao_historico_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."fornecedor_contatos"
    ADD CONSTRAINT "fornecedor_contatos_fornecedor_id_fkey" FOREIGN KEY ("fornecedor_id") REFERENCES "sueq"."fornecedores"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."inventario_ac"
    ADD CONSTRAINT "inventario_ac_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."inventario_movimentacoes"
    ADD CONSTRAINT "inventario_movimentacoes_inventario_unidade_id_fkey" FOREIGN KEY ("inventario_unidade_id") REFERENCES "sueq"."inventario_unidades"("id");

ALTER TABLE ONLY "sueq"."inventario_movimentacoes"
    ADD CONSTRAINT "inventario_movimentacoes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."inventario_movimentacoes"
    ADD CONSTRAINT "inventario_movimentacoes_unidade_destino_id_fkey" FOREIGN KEY ("unidade_destino_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."inventario_movimentacoes"
    ADD CONSTRAINT "inventario_movimentacoes_unidade_origem_id_fkey" FOREIGN KEY ("unidade_origem_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."inventario_unidades"
    ADD CONSTRAINT "inventario_unidades_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."inventario_unidades"
    ADD CONSTRAINT "inventario_unidades_unidade_atual_id_fkey" FOREIGN KEY ("unidade_atual_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."inventario_unidades"
    ADD CONSTRAINT "inventario_unidades_unidade_origem_id_fkey" FOREIGN KEY ("unidade_origem_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_ata_item_id_fkey" FOREIGN KEY ("ata_item_id") REFERENCES "sueq"."atas_itens"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "sueq"."categorias_licitacao"("id") ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id");

ALTER TABLE ONLY "sueq"."itens_entregas"
    ADD CONSTRAINT "itens_entregas_empenho_id_fkey" FOREIGN KEY ("empenho_id") REFERENCES "sueq"."empenhos"("id");

ALTER TABLE ONLY "sueq"."itens_entregas"
    ADD CONSTRAINT "itens_entregas_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."itens_entregas"
    ADD CONSTRAINT "itens_entregas_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id");

ALTER TABLE ONLY "sueq"."itens_entregas"
    ADD CONSTRAINT "itens_entregas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_entrega_id_fkey" FOREIGN KEY ("entrega_id") REFERENCES "sueq"."itens_entregas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id");

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."itens_entregas_unidades"
    ADD CONSTRAINT "itens_entregas_unidades_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_fornecedor_id_fkey" FOREIGN KEY ("fornecedor_id") REFERENCES "sueq"."fornecedores"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."itens_status_historico"
    ADD CONSTRAINT "itens_status_historico_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."itens_status_historico"
    ADD CONSTRAINT "itens_status_historico_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."itens_status_historico"
    ADD CONSTRAINT "itens_status_historico_status_id_fkey" FOREIGN KEY ("status_id") REFERENCES "sueq"."status_opcoes"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_status_lic_id_fkey" FOREIGN KEY ("status_lic_id") REFERENCES "sueq"."status_opcoes"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_status_lic_secretaria_id_fkey" FOREIGN KEY ("status_lic_secretaria_id") REFERENCES "sueq"."secretarias"("id");

ALTER TABLE ONLY "sueq"."itens"
    ADD CONSTRAINT "itens_unidade_destino_id_fkey" FOREIGN KEY ("unidade_destino_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_ocorrencia_id_fkey" FOREIGN KEY ("ocorrencia_id") REFERENCES "sueq"."licitacao_item_ocorrencias"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencia_emendas"
    ADD CONSTRAINT "licitacao_item_ocorrencia_emendas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencias"
    ADD CONSTRAINT "licitacao_item_ocorrencias_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencias"
    ADD CONSTRAINT "licitacao_item_ocorrencias_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id") ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."licitacao_item_ocorrencias"
    ADD CONSTRAINT "licitacao_item_ocorrencias_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."nf_checklist_documento_contratos"
    ADD CONSTRAINT "nf_checklist_documento_contratos_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nf_checklist_documento_contratos"
    ADD CONSTRAINT "nf_checklist_documento_contratos_documento_id_fkey" FOREIGN KEY ("documento_id") REFERENCES "sueq"."nf_checklist_documentos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nf_checklist_documento_contratos"
    ADD CONSTRAINT "nf_checklist_documento_contratos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."nf_checklist_documentos"
    ADD CONSTRAINT "nf_checklist_documentos_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nf_checklist_documentos"
    ADD CONSTRAINT "nf_checklist_documentos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."nf_checklist_marcacoes"
    ADD CONSTRAINT "nf_checklist_marcacoes_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nf_checklist_marcacoes"
    ADD CONSTRAINT "nf_checklist_marcacoes_documento_id_fkey" FOREIGN KEY ("documento_id") REFERENCES "sueq"."nf_checklist_documentos"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nf_checklist_marcacoes"
    ADD CONSTRAINT "nf_checklist_marcacoes_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_emenda_item_id_fkey" FOREIGN KEY ("emenda_item_id") REFERENCES "sueq"."emenda_itens"("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_empenho_id_fkey" FOREIGN KEY ("empenho_id") REFERENCES "sueq"."empenhos"("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_exec_id_fkey" FOREIGN KEY ("exec_id") REFERENCES "sueq"."atas_execucao"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_item_id_fkey" FOREIGN KEY ("item_id") REFERENCES "sueq"."itens"("id");

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."nota_fiscal_itens"
    ADD CONSTRAINT "nota_fiscal_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_emenda_id_fkey" FOREIGN KEY ("emenda_id") REFERENCES "sueq"."emendas"("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_fornecedor_id_fkey" FOREIGN KEY ("fornecedor_id") REFERENCES "sueq"."fornecedores"("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_medicao_id_fkey" FOREIGN KEY ("medicao_id") REFERENCES "sueq"."contratos_medicoes"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_processo_id_fkey" FOREIGN KEY ("processo_id") REFERENCES "sueq"."processos"("id");

ALTER TABLE ONLY "sueq"."notas_fiscais"
    ADD CONSTRAINT "notas_fiscais_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."pessoas"
    ADD CONSTRAINT "pessoas_usuario_id_fkey" FOREIGN KEY ("usuario_id") REFERENCES "sueq"."profiles"("id");

ALTER TABLE ONLY "sueq"."portal_inventario"
    ADD CONSTRAINT "portal_inventario_sala_unidade_fk" FOREIGN KEY ("sala_id", "unidade_id") REFERENCES "sueq"."portal_salas"("id", "unidade_id");

ALTER TABLE ONLY "sueq"."portal_inventario"
    ADD CONSTRAINT "portal_inventario_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_pedidos_itens"
    ADD CONSTRAINT "portal_pedidos_itens_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_pedidos_itens"
    ADD CONSTRAINT "portal_pedidos_sala_unidade_fk" FOREIGN KEY ("sala_id", "unidade_id") REFERENCES "sueq"."portal_salas"("id", "unidade_id");

ALTER TABLE ONLY "sueq"."portal_salas"
    ADD CONSTRAINT "portal_salas_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_inventario_origem_fk" FOREIGN KEY ("inventario_origem_id") REFERENCES "sueq"."portal_inventario"("id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_sala_destino_fk" FOREIGN KEY ("sala_destino_id", "unidade_destino_id") REFERENCES "sueq"."portal_salas"("id", "unidade_id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_unidade_destino_fk" FOREIGN KEY ("unidade_destino_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_transferencias_inventario"
    ADD CONSTRAINT "portal_transferencias_unidade_origem_fk" FOREIGN KEY ("unidade_origem_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_unidades_acessos"
    ADD CONSTRAINT "portal_unidades_acessos_unidade_id_fkey" FOREIGN KEY ("unidade_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."portal_unidades_acessos"
    ADD CONSTRAINT "portal_unidades_acessos_unidade_solicitada_id_fkey" FOREIGN KEY ("unidade_solicitada_id") REFERENCES "sueq"."unidades"("id");

ALTER TABLE ONLY "sueq"."processos"
    ADD CONSTRAINT "processos_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "sueq"."categorias_licitacao"("id") ON UPDATE CASCADE ON DELETE RESTRICT;

ALTER TABLE ONLY "sueq"."processos"
    ADD CONSTRAINT "processos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."profiles"
    ADD CONSTRAINT "profiles_contexto_divisao_id_fkey" FOREIGN KEY ("contexto_divisao_id") REFERENCES "sueq"."divisoes"("id");

ALTER TABLE ONLY "sueq"."profiles"
    ADD CONSTRAINT "profiles_contexto_secao_id_fkey" FOREIGN KEY ("contexto_secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."profiles"
    ADD CONSTRAINT "profiles_divisao_id_fkey" FOREIGN KEY ("divisao_id") REFERENCES "sueq"."divisoes"("id");

ALTER TABLE ONLY "sueq"."profiles"
    ADD CONSTRAINT "profiles_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."sancao_itens"
    ADD CONSTRAINT "sancao_itens_sancao_id_fkey" FOREIGN KEY ("sancao_id") REFERENCES "sueq"."sancoes_solicitadas"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."sancao_itens"
    ADD CONSTRAINT "sancao_itens_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."sancoes_administrativas"
    ADD CONSTRAINT "sancoes_administrativas_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."sancoes_administrativas"
    ADD CONSTRAINT "sancoes_administrativas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."sancoes_solicitadas"
    ADD CONSTRAINT "sancoes_solicitadas_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."sancoes_solicitadas"
    ADD CONSTRAINT "sancoes_solicitadas_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."secoes"
    ADD CONSTRAINT "secoes_divisao_id_fkey" FOREIGN KEY ("divisao_id") REFERENCES "sueq"."divisoes"("id");

ALTER TABLE ONLY "sueq"."termo_chamados"
    ADD CONSTRAINT "termo_chamados_chamado_id_fkey" FOREIGN KEY ("chamado_id") REFERENCES "sueq"."chamados"("id");

ALTER TABLE ONLY "sueq"."termo_chamados"
    ADD CONSTRAINT "termo_chamados_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."termo_chamados"
    ADD CONSTRAINT "termo_chamados_termo_id_fkey" FOREIGN KEY ("termo_id") REFERENCES "sueq"."termos_ateste"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."termo_contratos"
    ADD CONSTRAINT "termo_contratos_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."termo_contratos"
    ADD CONSTRAINT "termo_contratos_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."termo_contratos"
    ADD CONSTRAINT "termo_contratos_termo_id_fkey" FOREIGN KEY ("termo_id") REFERENCES "sueq"."termos_ateste"("id") ON DELETE CASCADE;

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_chamado_id_fkey" FOREIGN KEY ("chamado_id") REFERENCES "sueq"."chamados"("id");

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_contrato_id_fkey" FOREIGN KEY ("contrato_id") REFERENCES "sueq"."contratos"("id");

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_medicao_id_fkey" FOREIGN KEY ("medicao_id") REFERENCES "sueq"."contratos_medicoes"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_nota_fiscal_id_fkey" FOREIGN KEY ("nota_fiscal_id") REFERENCES "sueq"."notas_fiscais"("id") ON DELETE SET NULL;

ALTER TABLE ONLY "sueq"."termos_ateste"
    ADD CONSTRAINT "termos_ateste_secao_id_fkey" FOREIGN KEY ("secao_id") REFERENCES "sueq"."secoes"("id");

ALTER TABLE ONLY "sueq"."user_tab_permissions"
    ADD CONSTRAINT "user_tab_permissions_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "sueq"."profiles"("id") ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_ata_item_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("ata_item_id") WHERE ("ata_item_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_contrato_fk_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("contrato_id") WHERE ("contrato_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_emenda_fk_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_execucao_fk_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("ata_execucao_id") WHERE ("ata_execucao_id" IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS "ata_planejamento_emendas_item_ativo_uidx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("emenda_item_id") WHERE ("status" <> 'CANCELADO'::"text");

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_processo_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("processo_id", "processo_item_id");

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_processo_item_fk_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("processo_item_id");

CREATE INDEX IF NOT EXISTS "ata_planejamento_emendas_secao_fk_idx" ON "sueq"."ata_planejamento_emendas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "atas_execucao_reajustes_emenda_idx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("emenda_id") WHERE ("emenda_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "atas_execucao_reajustes_emenda_item_idx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("emenda_item_id") WHERE ("emenda_item_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "atas_execucao_reajustes_empenho_idx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("empenho_id");

CREATE INDEX IF NOT EXISTS "atas_execucao_reajustes_execucao_idx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("ata_execucao_id", "criado_em" DESC);

CREATE INDEX IF NOT EXISTS "atas_execucao_reajustes_secao_idx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("secao_id");

CREATE UNIQUE INDEX IF NOT EXISTS "atas_execucao_reajustes_unico_ativo_uidx" ON "sueq"."atas_execucao_reajustes" USING "btree" ("ata_reajuste_id", "ata_execucao_id") WHERE ("status" = 'ATIVO'::"text");

CREATE INDEX IF NOT EXISTS "atas_item_marca_apostilamentos_contrato_idx" ON "sueq"."atas_item_marca_apostilamentos" USING "btree" ("contrato_id", "data_apostilamento" DESC);

CREATE INDEX IF NOT EXISTS "atas_item_marca_apostilamentos_item_idx" ON "sueq"."atas_item_marca_apostilamentos" USING "btree" ("ata_item_id", "data_apostilamento" DESC, "criado_em" DESC);

CREATE INDEX IF NOT EXISTS "atas_item_marca_apostilamentos_secao_idx" ON "sueq"."atas_item_marca_apostilamentos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "atas_item_reajustes_contrato_idx" ON "sueq"."atas_item_reajustes" USING "btree" ("contrato_id", "data_vigencia" DESC);

CREATE INDEX IF NOT EXISTS "atas_item_reajustes_item_idx" ON "sueq"."atas_item_reajustes" USING "btree" ("ata_item_id", "data_vigencia" DESC);

CREATE UNIQUE INDEX IF NOT EXISTS "atas_item_reajustes_item_vigencia_ativo_uidx" ON "sueq"."atas_item_reajustes" USING "btree" ("ata_item_id", "data_vigencia") WHERE ("status" = 'ATIVO'::"text");

CREATE INDEX IF NOT EXISTS "atas_item_reajustes_secao_idx" ON "sueq"."atas_item_reajustes" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "atas_itens_categoria_id_idx" ON "sueq"."atas_itens" USING "btree" ("categoria_id");

CREATE INDEX IF NOT EXISTS "categorias_licitacao_ativas_ordem_idx" ON "sueq"."categorias_licitacao" USING "btree" ("ativo", "ordem", "nome");

CREATE UNIQUE INDEX IF NOT EXISTS "categorias_licitacao_nome_chave_uidx" ON "sueq"."categorias_licitacao" USING "btree" ("nome_chave");

CREATE UNIQUE INDEX IF NOT EXISTS "chamados_controle_chamado_id_key" ON "sueq"."chamados_controle" USING "btree" ("chamado_id") WHERE ("chamado_id" IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS "chamados_request_id_key" ON "sueq"."chamados" USING "btree" ("request_id") WHERE ("request_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "contratos_categoria_id_idx" ON "sueq"."contratos" USING "btree" ("categoria_id");

CREATE INDEX IF NOT EXISTS "contratos_tipo_instrumento_idx" ON "sueq"."contratos" USING "btree" ("tipo_instrumento");

CREATE UNIQUE INDEX IF NOT EXISTS "empenho_itens_exec_id_uq" ON "sueq"."empenho_itens" USING "btree" ("exec_id") WHERE ("exec_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "entregas_observacoes_ata_execucao_idx" ON "sueq"."entregas_observacoes" USING "btree" ("ata_execucao_id", "created_at");

CREATE INDEX IF NOT EXISTS "entregas_observacoes_autor_idx" ON "sueq"."entregas_observacoes" USING "btree" ("autor_id");

CREATE INDEX IF NOT EXISTS "entregas_observacoes_item_entrega_idx" ON "sueq"."entregas_observacoes" USING "btree" ("item_entrega_id", "created_at");

CREATE INDEX IF NOT EXISTS "entregas_observacoes_item_idx" ON "sueq"."entregas_observacoes" USING "btree" ("item_id", "created_at");

CREATE INDEX IF NOT EXISTS "entregas_observacoes_secao_idx" ON "sueq"."entregas_observacoes" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "entregas_observacoes_updated_by_idx" ON "sueq"."entregas_observacoes" USING "btree" ("updated_by");

CREATE INDEX IF NOT EXISTS "entregas_prazos_historico_alterado_por_idx" ON "sueq"."entregas_prazos_historico" USING "btree" ("alterado_por");

CREATE INDEX IF NOT EXISTS "entregas_prazos_historico_ata_idx" ON "sueq"."entregas_prazos_historico" USING "btree" ("ata_execucao_id", "created_at");

CREATE INDEX IF NOT EXISTS "entregas_prazos_historico_item_idx" ON "sueq"."entregas_prazos_historico" USING "btree" ("item_entrega_id", "created_at");

CREATE INDEX IF NOT EXISTS "idx_aeu_ata_item" ON "sueq"."atas_execucao_unidades" USING "btree" ("ata_item_id");

CREATE INDEX IF NOT EXISTS "idx_aeu_emenda_item" ON "sueq"."atas_execucao_unidades" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_aeu_exec" ON "sueq"."atas_execucao_unidades" USING "btree" ("exec_id");

CREATE INDEX IF NOT EXISTS "idx_aeu_nf" ON "sueq"."atas_execucao_unidades" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_ata_item_id" ON "sueq"."atas_execucao" USING "btree" ("ata_item_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_emenda" ON "sueq"."atas_execucao" USING "btree" ("emenda_id") WHERE ("emenda_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_emenda_id" ON "sueq"."atas_execucao" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_emenda_item_id" ON "sueq"."atas_execucao" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_secao_id" ON "sueq"."atas_execucao" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_unidades_secao_id" ON "sueq"."atas_execucao_unidades" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_atas_execucao_unidades_unidade_id" ON "sueq"."atas_execucao_unidades" USING "btree" ("unidade_id");

CREATE INDEX IF NOT EXISTS "idx_atas_itens_codigo_siam" ON "sueq"."atas_itens" USING "btree" ("codigo_siam") WHERE ("codigo_siam" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_atas_itens_contrato_id" ON "sueq"."atas_itens" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_atas_itens_secao_id" ON "sueq"."atas_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_anexos_chamado_id" ON "sueq"."chamados_anexos" USING "btree" ("chamado_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_anexos_secao_id" ON "sueq"."chamados_anexos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_contrato_id" ON "sueq"."chamados" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_chamado_id" ON "sueq"."chamados_controle" USING "btree" ("chamado_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_contrato_id" ON "sueq"."chamados_controle" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_medicao" ON "sueq"."chamados_controle" USING "btree" ("medicao_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_nota_fiscal" ON "sueq"."chamados_controle" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_secao_id" ON "sueq"."chamados_controle" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_controle_termo_ateste" ON "sueq"."chamados_controle" USING "btree" ("termo_ateste_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_secao_id" ON "sueq"."chamados" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_chamados_unidade_id" ON "sueq"."chamados" USING "btree" ("unidade_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_fiscalizadores_contrato_id" ON "sueq"."contratos_fiscalizadores" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_fiscalizadores_secao_id" ON "sueq"."contratos_fiscalizadores" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_fornecedor_id" ON "sueq"."contratos" USING "btree" ("fornecedor_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_historico_contrato_id" ON "sueq"."contratos_historico" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_historico_secao_id" ON "sueq"."contratos_historico" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_glosas_contrato" ON "sueq"."contratos_medicao_glosas" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_glosas_item" ON "sueq"."contratos_medicao_glosas" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_glosas_medicao" ON "sueq"."contratos_medicao_glosas" USING "btree" ("medicao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_glosas_secao_id" ON "sueq"."contratos_medicao_glosas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_itens_contrato" ON "sueq"."contratos_medicao_itens" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_itens_item" ON "sueq"."contratos_medicao_itens" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_itens_medicao" ON "sueq"."contratos_medicao_itens" USING "btree" ("medicao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicao_itens_secao_id" ON "sueq"."contratos_medicao_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicoes_ciclo" ON "sueq"."contratos_medicoes" USING "btree" ("contrato_id", "ciclo_numero");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicoes_competencia" ON "sueq"."contratos_medicoes" USING "btree" ("competencia");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicoes_contrato" ON "sueq"."contratos_medicoes" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicoes_secao_id" ON "sueq"."contratos_medicoes" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_medicoes_status" ON "sueq"."contratos_medicoes" USING "btree" ("status");

CREATE INDEX IF NOT EXISTS "idx_contratos_periodicidade_pagamento" ON "sueq"."contratos" USING "btree" ("periodicidade_pagamento");

CREATE INDEX IF NOT EXISTS "idx_contratos_processo_id" ON "sueq"."contratos" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_secao_id" ON "sueq"."contratos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_vigencias_contrato_id" ON "sueq"."contratos_vigencias" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_contratos_vigencias_secao_id" ON "sueq"."contratos_vigencias" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_emenda_id" ON "sueq"."emenda_itens" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_processo_id" ON "sueq"."emenda_itens" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_secao_id" ON "sueq"."emenda_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_status_id" ON "sueq"."emenda_itens" USING "btree" ("status_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_unidade_beneficiada_id" ON "sueq"."emenda_itens" USING "btree" ("unidade_beneficiada_id");

CREATE INDEX IF NOT EXISTS "idx_emenda_itens_unidade_entrega_id" ON "sueq"."emenda_itens" USING "btree" ("unidade_entrega_id");

CREATE INDEX IF NOT EXISTS "idx_emendas_secao_id" ON "sueq"."emendas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_emendas_unidade_id" ON "sueq"."emendas" USING "btree" ("unidade_id");

CREATE INDEX IF NOT EXISTS "idx_empenho_itens_emenda_id" ON "sueq"."empenho_itens" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_empenho_itens_emenda_item_id" ON "sueq"."empenho_itens" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_empenho_itens_empenho_id" ON "sueq"."empenho_itens" USING "btree" ("empenho_id");

CREATE INDEX IF NOT EXISTS "idx_empenho_itens_item_id" ON "sueq"."empenho_itens" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_empenho_itens_secao_id" ON "sueq"."empenho_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_empenhos_contrato_id" ON "sueq"."empenhos" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_empenhos_emenda_id" ON "sueq"."empenhos" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_empenhos_fornecedor_id" ON "sueq"."empenhos" USING "btree" ("fornecedor_id");

CREATE INDEX IF NOT EXISTS "idx_empenhos_processo_id" ON "sueq"."empenhos" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_empenhos_secao_id" ON "sueq"."empenhos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_fiscalizacao_historico_chamado_id" ON "sueq"."fiscalizacao_historico" USING "btree" ("chamado_id");

CREATE INDEX IF NOT EXISTS "idx_fiscalizacao_historico_contrato_id" ON "sueq"."fiscalizacao_historico" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_fiscalizacao_historico_secao_id" ON "sueq"."fiscalizacao_historico" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_fornecedor_contatos_fornecedor_id" ON "sueq"."fornecedor_contatos" USING "btree" ("fornecedor_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_ac_secao_id" ON "sueq"."inventario_ac" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_movimentacoes_secao" ON "sueq"."inventario_movimentacoes" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_movimentacoes_unidade_data" ON "sueq"."inventario_movimentacoes" USING "btree" ("inventario_unidade_id", "data_movimentacao" DESC, "criado_em" DESC);

CREATE INDEX IF NOT EXISTS "idx_inventario_movimentacoes_unidade_destino" ON "sueq"."inventario_movimentacoes" USING "btree" ("unidade_destino_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_movimentacoes_unidade_origem" ON "sueq"."inventario_movimentacoes" USING "btree" ("unidade_origem_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_unidades_atual" ON "sueq"."inventario_unidades" USING "btree" ("unidade_atual_id", "situacao_atual");

CREATE INDEX IF NOT EXISTS "idx_inventario_unidades_secao" ON "sueq"."inventario_unidades" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_inventario_unidades_unidade_origem" ON "sueq"."inventario_unidades" USING "btree" ("unidade_origem_id");

CREATE INDEX IF NOT EXISTS "idx_itens_ata_item_id" ON "sueq"."itens" USING "btree" ("ata_item_id");

CREATE INDEX IF NOT EXISTS "idx_itens_codigo_siam" ON "sueq"."itens" USING "btree" ("codigo_siam") WHERE ("codigo_siam" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_itens_contrato_id" ON "sueq"."itens" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_itens_emenda_id" ON "sueq"."itens" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_itens_emenda_item_id" ON "sueq"."itens" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_empenho_id" ON "sueq"."itens_entregas" USING "btree" ("empenho_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_item_id" ON "sueq"."itens_entregas" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_nota_fiscal_id" ON "sueq"."itens_entregas" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_secao_id" ON "sueq"."itens_entregas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_unidades_entrega_id" ON "sueq"."itens_entregas_unidades" USING "btree" ("entrega_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_unidades_item_id" ON "sueq"."itens_entregas_unidades" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_unidades_nota_fiscal_id" ON "sueq"."itens_entregas_unidades" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_unidades_secao_id" ON "sueq"."itens_entregas_unidades" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_itens_entregas_unidades_unidade_id" ON "sueq"."itens_entregas_unidades" USING "btree" ("unidade_id");

CREATE INDEX IF NOT EXISTS "idx_itens_fornecedor_id" ON "sueq"."itens" USING "btree" ("fornecedor_id");

CREATE INDEX IF NOT EXISTS "idx_itens_processo_id" ON "sueq"."itens" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_itens_secao_id" ON "sueq"."itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_itens_status_historico_item_id" ON "sueq"."itens_status_historico" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_itens_status_historico_mudado_por" ON "sueq"."itens_status_historico" USING "btree" ("mudado_por");

CREATE INDEX IF NOT EXISTS "idx_itens_status_historico_secao_id" ON "sueq"."itens_status_historico" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_itens_status_historico_status_id" ON "sueq"."itens_status_historico" USING "btree" ("status_id");

CREATE INDEX IF NOT EXISTS "idx_itens_status_lic_id" ON "sueq"."itens" USING "btree" ("status_lic_id");

CREATE INDEX IF NOT EXISTS "idx_itens_status_lic_secretaria_id" ON "sueq"."itens" USING "btree" ("status_lic_secretaria_id") WHERE ("status_lic_secretaria_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_itens_unidade_destino_id" ON "sueq"."itens" USING "btree" ("unidade_destino_id");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencia_emendas_emenda" ON "sueq"."licitacao_item_ocorrencia_emendas" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencia_emendas_emenda_item" ON "sueq"."licitacao_item_ocorrencia_emendas" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencia_emendas_secao" ON "sueq"."licitacao_item_ocorrencia_emendas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencias_criado_por" ON "sueq"."licitacao_item_ocorrencias" USING "btree" ("criado_por");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencias_processo" ON "sueq"."licitacao_item_ocorrencias" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_licitacao_item_ocorrencias_secao" ON "sueq"."licitacao_item_ocorrencias" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_documento_contratos_contrato" ON "sueq"."nf_checklist_documento_contratos" USING "btree" ("contrato_id", "documento_id");

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_documento_contratos_secao" ON "sueq"."nf_checklist_documento_contratos" USING "btree" ("secao_id", "documento_id");

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_documentos_contrato" ON "sueq"."nf_checklist_documentos" USING "btree" ("contrato_id") WHERE ("contrato_id" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_documentos_created_by" ON "sueq"."nf_checklist_documentos" USING "btree" ("created_by") WHERE ("created_by" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_documentos_secao_ordem" ON "sueq"."nf_checklist_documentos" USING "btree" ("secao_id", "ativo", "ordem", "nome");

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_marcacoes_documento" ON "sueq"."nf_checklist_marcacoes" USING "btree" ("documento_id");

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_marcacoes_marcado_por" ON "sueq"."nf_checklist_marcacoes" USING "btree" ("marcado_por") WHERE ("marcado_por" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "idx_nf_checklist_marcacoes_mes" ON "sueq"."nf_checklist_marcacoes" USING "btree" ("secao_id", "competencia", "contrato_id");

CREATE INDEX IF NOT EXISTS "idx_nf_contrato_fornecedor_numero_norm" ON "sueq"."notas_fiscais" USING "btree" ("contrato_id", COALESCE("fornecedor_id", (0)::bigint), COALESCE("numero_normalizado", "regexp_replace"(COALESCE("numero", ''::"text"), '\D'::"text", ''::"text", 'g'::"text"))) WHERE (("contrato_id" IS NOT NULL) AND ("numero" IS NOT NULL));

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_emenda_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_emenda_item_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("emenda_item_id");

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_empenho_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("empenho_id");

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_item_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("item_id");

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_nota_fiscal_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_nota_fiscal_itens_secao_id" ON "sueq"."nota_fiscal_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_contrato_id" ON "sueq"."notas_fiscais" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_emenda_id" ON "sueq"."notas_fiscais" USING "btree" ("emenda_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_fornecedor_id" ON "sueq"."notas_fiscais" USING "btree" ("fornecedor_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_medicao" ON "sueq"."notas_fiscais" USING "btree" ("medicao_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_processo_id" ON "sueq"."notas_fiscais" USING "btree" ("processo_id");

CREATE INDEX IF NOT EXISTS "idx_notas_fiscais_secao_id" ON "sueq"."notas_fiscais" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_pessoas_usuario_id" ON "sueq"."pessoas" USING "btree" ("usuario_id");

CREATE INDEX IF NOT EXISTS "idx_processos_secao_id" ON "sueq"."processos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_profiles_contexto_divisao_id" ON "sueq"."profiles" USING "btree" ("contexto_divisao_id");

CREATE INDEX IF NOT EXISTS "idx_profiles_contexto_secao_id" ON "sueq"."profiles" USING "btree" ("contexto_secao_id");

CREATE INDEX IF NOT EXISTS "idx_profiles_divisao_id" ON "sueq"."profiles" USING "btree" ("divisao_id");

CREATE INDEX IF NOT EXISTS "idx_profiles_secao_id" ON "sueq"."profiles" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_sancao_itens_sancao_id" ON "sueq"."sancao_itens" USING "btree" ("sancao_id");

CREATE INDEX IF NOT EXISTS "idx_sancao_itens_secao_id" ON "sueq"."sancao_itens" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_sancoes_administrativas_contrato_id" ON "sueq"."sancoes_administrativas" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_sancoes_administrativas_secao_id" ON "sueq"."sancoes_administrativas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_sancoes_solicitadas_contrato_id" ON "sueq"."sancoes_solicitadas" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_sancoes_solicitadas_secao_id" ON "sueq"."sancoes_solicitadas" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_secoes_divisao_id" ON "sueq"."secoes" USING "btree" ("divisao_id");

CREATE INDEX IF NOT EXISTS "idx_termo_chamados_chamado_id" ON "sueq"."termo_chamados" USING "btree" ("chamado_id");

CREATE INDEX IF NOT EXISTS "idx_termo_chamados_secao_id" ON "sueq"."termo_chamados" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_termo_chamados_termo_id" ON "sueq"."termo_chamados" USING "btree" ("termo_id");

CREATE INDEX IF NOT EXISTS "idx_termo_contratos_contrato_id" ON "sueq"."termo_contratos" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_termo_contratos_secao_id" ON "sueq"."termo_contratos" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "idx_termo_contratos_termo_id" ON "sueq"."termo_contratos" USING "btree" ("termo_id");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_chamado_id" ON "sueq"."termos_ateste" USING "btree" ("chamado_id");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_competencia" ON "sueq"."termos_ateste" USING "btree" ("competencia");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_contrato_id" ON "sueq"."termos_ateste" USING "btree" ("contrato_id");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_medicao" ON "sueq"."termos_ateste" USING "btree" ("medicao_id");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_nota_fiscal" ON "sueq"."termos_ateste" USING "btree" ("nota_fiscal_id");

CREATE INDEX IF NOT EXISTS "idx_termos_ateste_secao_id" ON "sueq"."termos_ateste" USING "btree" ("secao_id");

CREATE INDEX IF NOT EXISTS "itens_categoria_id_idx" ON "sueq"."itens" USING "btree" ("categoria_id");

CREATE INDEX IF NOT EXISTS "nota_fiscal_itens_exec_id_idx" ON "sueq"."nota_fiscal_itens" USING "btree" ("exec_id") WHERE ("exec_id" IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS "nota_fiscal_itens_nf_exec_emp_uq" ON "sueq"."nota_fiscal_itens" USING "btree" ("nota_fiscal_id", "exec_id", "empenho_id") WHERE (("exec_id" IS NOT NULL) AND ("empenho_id" IS NOT NULL));

CREATE INDEX IF NOT EXISTS "portal_acessos_revisado_por_idx" ON "sueq"."portal_unidades_acessos" USING "btree" ("revisado_por");

CREATE INDEX IF NOT EXISTS "portal_acessos_unidade_idx" ON "sueq"."portal_unidades_acessos" USING "btree" ("unidade_id");

CREATE INDEX IF NOT EXISTS "portal_acessos_unidade_solicitada_idx" ON "sueq"."portal_unidades_acessos" USING "btree" ("unidade_solicitada_id");

CREATE INDEX IF NOT EXISTS "portal_inventario_atualizado_por_idx" ON "sueq"."portal_inventario" USING "btree" ("atualizado_por");

CREATE INDEX IF NOT EXISTS "portal_inventario_criado_por_idx" ON "sueq"."portal_inventario" USING "btree" ("criado_por");

CREATE INDEX IF NOT EXISTS "portal_inventario_sala_idx" ON "sueq"."portal_inventario" USING "btree" ("sala_id", "ativo");

CREATE INDEX IF NOT EXISTS "portal_inventario_sala_unidade_idx" ON "sueq"."portal_inventario" USING "btree" ("sala_id", "unidade_id");

CREATE INDEX IF NOT EXISTS "portal_inventario_unidade_ativo_item_idx" ON "sueq"."portal_inventario" USING "btree" ("unidade_id", "ativo", "item_nome");

CREATE INDEX IF NOT EXISTS "portal_inventario_unidade_idx" ON "sueq"."portal_inventario" USING "btree" ("unidade_id", "ativo");

CREATE INDEX IF NOT EXISTS "portal_pedidos_atualizado_por_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("atualizado_por");

CREATE UNIQUE INDEX IF NOT EXISTS "portal_pedidos_client_request_id_uq" ON "sueq"."portal_pedidos_itens" USING "btree" ("client_request_id");

CREATE INDEX IF NOT EXISTS "portal_pedidos_criado_por_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("criado_por");

CREATE INDEX IF NOT EXISTS "portal_pedidos_item_ativo_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("lower"(TRIM(BOTH FROM "item_nome"))) WHERE ("status" = 'ATIVO'::"text");

CREATE INDEX IF NOT EXISTS "portal_pedidos_sala_unidade_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("sala_id", "unidade_id");

CREATE INDEX IF NOT EXISTS "portal_pedidos_unidade_status_atualizado_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("unidade_id", "status", "atualizado_em" DESC);

CREATE INDEX IF NOT EXISTS "portal_pedidos_unidade_status_idx" ON "sueq"."portal_pedidos_itens" USING "btree" ("unidade_id", "status");

CREATE INDEX IF NOT EXISTS "portal_salas_criado_por_idx" ON "sueq"."portal_salas" USING "btree" ("criado_por");

CREATE UNIQUE INDEX IF NOT EXISTS "portal_salas_unidade_nome_ativo_uq" ON "sueq"."portal_salas" USING "btree" ("unidade_id", "lower"(TRIM(BOTH FROM "nome"))) WHERE ("ativo" IS TRUE);

CREATE INDEX IF NOT EXISTS "portal_transferencias_cancelado_por_idx" ON "sueq"."portal_transferencias_inventario" USING "btree" ("cancelado_por") WHERE ("cancelado_por" IS NOT NULL);

CREATE INDEX IF NOT EXISTS "portal_transferencias_destino_status_idx" ON "sueq"."portal_transferencias_inventario" USING "btree" ("unidade_destino_id", "status", "enviado_em" DESC);

CREATE INDEX IF NOT EXISTS "portal_transferencias_origem_status_idx" ON "sueq"."portal_transferencias_inventario" USING "btree" ("unidade_origem_id", "status", "enviado_em" DESC);

CREATE INDEX IF NOT EXISTS "portal_transferencias_sala_destino_idx" ON "sueq"."portal_transferencias_inventario" USING "btree" ("sala_destino_id", "unidade_destino_id");

CREATE INDEX IF NOT EXISTS "processos_categoria_id_idx" ON "sueq"."processos" USING "btree" ("categoria_id");

CREATE UNIQUE INDEX IF NOT EXISTS "uq_atas_execucao_unidades_exec_seq" ON "sueq"."atas_execucao_unidades" USING "btree" ("exec_id", "unidade_seq");

CREATE UNIQUE INDEX IF NOT EXISTS "uq_itens_entregas_item_af_ativa" ON "sueq"."itens_entregas" USING "btree" ("item_id", "lower"("btrim"("af_numero"))) WHERE ((NULLIF("btrim"("af_numero"), ''::"text") IS NOT NULL) AND (COALESCE("status", ''::"text") <> 'cancelada'::"text"));

CREATE UNIQUE INDEX IF NOT EXISTS "uq_itens_entregas_unidades_entrega_seq" ON "sueq"."itens_entregas_unidades" USING "btree" ("entrega_id", "unidade_seq");

CREATE UNIQUE INDEX IF NOT EXISTS "uq_nf_checklist_documentos_ativos" ON "sueq"."nf_checklist_documentos" USING "btree" ("secao_id", "lower"("btrim"("nome"))) WHERE ("ativo" IS TRUE);

CREATE UNIQUE INDEX IF NOT EXISTS "uq_notas_fiscais_medicao" ON "sueq"."notas_fiscais" USING "btree" ("medicao_id") WHERE ("medicao_id" IS NOT NULL);

ALTER TABLE sueq.emendas ADD COLUMN IF NOT EXISTS link_sei text;
