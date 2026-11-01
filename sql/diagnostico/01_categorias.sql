-- Quais categorias existem, quantas vitórias cada uma tem e em que período.
-- Confere se alguma categoria principal ficou com nome diferente de 500cc/MotoGP.
SELECT
    class_name,
    is_premier_class,
    COUNT(*)    AS vitorias,
    MIN(season) AS primeira,
    MAX(season) AS ultima
FROM refined.race_wins
GROUP BY class_name, is_premier_class
ORDER BY primeira, class_name;
