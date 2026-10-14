-- Индексы для ускорения поиска и связей
CREATE INDEX IF NOT EXISTS idx_chart_date ON chart_records(date);
CREATE INDEX IF NOT EXISTS idx_chart_region ON chart_records(region);