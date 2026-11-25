-- Example data for the items table (run by /seed). Safe to run many times:
-- rows are only inserted when no item with the same name exists.
-- The vectors have 3 values and require EMBEDDING_DIM=3.

INSERT INTO items (name, description, embedding)
SELECT v.name, v.description, v.embedding::vector
FROM (VALUES
    ('Apple',   'Fruit, red or green',        '[0.9, 0.1, 0.0]'),
    ('Banana',  'Fruit, yellow',              '[0.8, 0.2, 0.1]'),
    ('Carrot',  'Vegetable, orange',          '[0.2, 0.9, 0.1]'),
    ('Laptop',  'Computer, portable',         '[0.0, 0.1, 0.9]'),
    ('Phone',   'Computer, fits in a pocket', '[0.1, 0.0, 0.8]'),
    ('Notebook', 'Paper, no vector yet',      NULL)
) AS v(name, description, embedding)
WHERE NOT EXISTS (SELECT 1 FROM items i WHERE i.name = v.name);

SELECT count(*) AS items_total FROM items;
