-- ============================================
-- Триггеры для автоматизации бизнес-логики
-- ============================================

-- Триггер для продления опроса при попытке закрытия
-- Срабатывает перед обновлением статуса опроса
CREATE TRIGGER TRIGGER_PRODLENIE_OPROSA_PRI_ZAKRYTII
    BEFORE UPDATE OF STATUS ON OPROS
    FOR EACH ROW
    WHEN (NEW.STATUS = 'closed' AND OLD.STATUS != 'closed')
    EXECUTE FUNCTION PRODLENIE_OPROSA_ESLI_NEKHVATAET();

COMMENT ON TRIGGER TRIGGER_PRODLENIE_OPROSA_PRI_ZAKRYTII ON OPROS IS 
'Триггер продления опроса. Срабатывает при попытке перевести статус в "closed".
Если участников недостаточно (считается по UCHASTIE), опрос автоматически продлевается и остаётся активным.';
