CREATE TABLE "Stores" (
	"STORE_ID"	INTEGER NOT NULL UNIQUE,
	"STORE_NAME"	TEXT NOT NULL,
	"URL"	TEXT NOT NULL UNIQUE,
	PRIMARY KEY("STORE_ID" AUTOINCREMENT)
);