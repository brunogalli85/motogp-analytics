-- Resultados principais para a seção "Resultados" do README.
-- Lê somente a camada marts.

-- 1. Fabricante líder de cada década (categoria principal)
SELECT decade, constructor_name, wins, share_pct
FROM marts.constructor_wins_by_decade
WHERE rank_in_decade = 1
ORDER BY decade;

-- 2. Temporadas de maior domínio do fabricante campeão
SELECT season, champion_constructor, champion_wins, season_races, champion_win_pct
FROM marts.champion_dominance
ORDER BY champion_win_pct DESC, season
LIMIT 10;

-- 3. Top 10 pilotos da categoria principal
SELECT rank_position, rider_name, country_code, wins, first_win_season, last_win_season
FROM marts.top_riders_premier
WHERE rank_position <= 10;

-- 4. País líder de cada década (todas as categorias)
SELECT decade, country_code, wins, share_pct
FROM marts.wins_by_country_decade
WHERE rank_in_decade = 1
ORDER BY decade;

-- 5. Países com mais pódios de uma só nacionalidade
SELECT nation_code, SUM(lockouts) AS pódios
FROM marts.podium_lockouts_by_nation
GROUP BY nation_code
ORDER BY pódios DESC
LIMIT 5;
