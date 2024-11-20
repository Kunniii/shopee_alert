const sqlite3 = require('sqlite3').verbose();

const db = new sqlite3.Database('./database.sqlite');

db.serialize(() => {
    db.run(`
        CREATE TABLE IF NOT EXISTS ship_providers (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NAME TEXT UNIQUE NOT NULL,
            URL TEXT
        )
    `, (err) => {
        if (err) {
            console.error("Error creating ship_providers table:", err.message);
        } else {
            console.log("ship_providers table created or already exists.");
        }
    });

    db.run(`
        CREATE TABLE IF NOT EXISTS shipments (
            ID TEXT PRIMARY KEY,
            CODE TEXT UNIQUE NOT NULL,
            PROVIDER_ID INTEGER NOT NULL,
            STATUS INTEGER NOT NULL,
            FOREIGN KEY (PROVIDER_ID) REFERENCES ship_providers(ID)
        )
    `, (err) => {
        if (err) {
            console.error("Error creating shipments table:", err.message);
        } else {
            console.log("shipments table created or already exists.");
        }
    });

    db.run(`INSERT INTO ship_providers (NAME, URL) VALUES ('GHN', 'https://donhang.ghn.vn/?order_code=$$CODE$$')`, (err) => {
        if (err) {
            console.error("Error inserting sample data:", err.message);
        }
    });
    db.run(`INSERT INTO ship_providers (NAME, URL) VALUES ('SPX', 'https://spx.vn/track?$$CODE$$')`, (err) => {
        if (err) {
            console.error("Error inserting sample data:", err.message);
        }
    });
});

db.close((err) => {
    if (err) {
        console.error("Error closing database:", err.message);
    } else {
        console.log("Database closed.");
    }
});