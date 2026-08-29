-- Permite enunciados longos (ex.: descrição do procedimento, blocos informativos)
ALTER TABLE perguntas_protocolo ALTER COLUMN enunciado TYPE TEXT USING enunciado::TEXT;
