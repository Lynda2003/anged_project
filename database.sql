-- ==============================
-- Base de données ANGed
-- ==============================

CREATE DATABASE anged_db;

-- ==============================
-- Table: users
-- ==============================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nom VARCHAR(100) NOT NULL,
    prenom VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'user',
    actif BOOLEAN DEFAULT TRUE,
    reset_token VARCHAR(255),
    reset_token_expiry TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table: cahiers_charge
-- ==============================
CREATE TABLE cahiers_charge (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    titre VARCHAR(255) NOT NULL,
    nom_entreprise VARCHAR(255),
    donnees_formulaire JSONB,
    statut VARCHAR(20) DEFAULT 'brouillon',
    fichier_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table: depots
-- ==============================
CREATE TABLE depots (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    nom_depot VARCHAR(255) NOT NULL,
    adresse TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table: documents
-- ==============================
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    depot_id INTEGER REFERENCES depots(id) ON DELETE CASCADE,
    type_doc VARCHAR(20) NOT NULL,
    fichier_nom VARCHAR(255),
    fichier_path VARCHAR(500),
    statut_verif VARCHAR(20) DEFAULT 'en_attente',
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Table: suivis
-- ==============================
CREATE TABLE suivis (
    id SERIAL PRIMARY KEY,
    depot_id INTEGER REFERENCES depots(id) ON DELETE CASCADE,
    admin_id INTEGER REFERENCES users(id),
    statut VARCHAR(20) NOT NULL,
    commentaire TEXT,
    date_verification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ==============================
-- Index
-- ==============================
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_cahiers_user ON cahiers_charge(user_id);
CREATE INDEX idx_documents_depot ON documents(depot_id);
CREATE INDEX idx_suivis_depot ON suivis(depot_id);


INSERT INTO users (email, password, nom, prenom, role)
VALUES ('admin@test.com', '1234', 'Admin', 'Root', 'admin');
