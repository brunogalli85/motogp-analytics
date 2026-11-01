-- Pergunta 5: quais países fecharam pódios inteiros só com seus pilotos, e em que décadas?

DROP TABLE IF EXISTS marts.podium_lockouts_by_nation;

CREATE TABLE marts.podium_lockouts_by_nation AS
SELECT
    (season / 10) * 10          AS decade,
    COALESCE(nation_code, 'N/D') AS nation_code,
    COUNT(*)                    AS lockouts,
    SUM(is_premier_class)       AS premier_class_lockouts
FROM refined.podium_lockouts
GROUP BY 1, 2
ORDER BY decade, lockouts DESC;
