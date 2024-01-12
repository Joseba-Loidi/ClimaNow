-- Crear la base de datos si no existe
CREATE DATABASE IF NOT EXISTS ClimaNow;

-- Seleccionar la base de datos
USE ClimaNow;

-- Crear la tabla users si no existe
CREATE TABLE IF NOT EXISTS users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(255) NOT NULL,
  password VARCHAR(255) NOT NULL,
  mail VARCHAR(255) NOT NULL,
  jwt VARCHAR(255) DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS favorites (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    location VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id)
);
