
CREATE DATABASE IF NOT EXISTS glowguide;
USE glowguide;

-- 1. Users
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Products
CREATE TABLE IF NOT EXISTS products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(150) NOT NULL,
    brand VARCHAR(100),
    category VARCHAR(100),
    description TEXT,
    skin_type VARCHAR(255),
    skin_concerns VARCHAR(255),
    ingredients TEXT,
    price DECIMAL(10,2),
    image_path VARCHAR(255),
    usage_instructions TEXT,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. User preferences
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    skin_type VARCHAR(50) NOT NULL,
    skin_concerns VARCHAR(255),
    budget DECIMAL(10,2),
    avoid_ingredients TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 4. Ingredients
CREATE TABLE IF NOT EXISTS ingredients (
    ingredient_id INT AUTO_INCREMENT PRIMARY KEY,
    ingredient_name VARCHAR(150) NOT NULL UNIQUE,
    description TEXT
);

-- 5. Product ingredients
CREATE TABLE IF NOT EXISTS product_ingredients (
    product_id INT NOT NULL,
    ingredient_id INT NOT NULL,
    ingredient_role VARCHAR(100),
    PRIMARY KEY (product_id, ingredient_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
        ON DELETE CASCADE
);

-- 6. Recommendations
CREATE TABLE IF NOT EXISTS recommendations (
    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    recommendation_reason TEXT,
    score DECIMAL(5,2),
    recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
        ON DELETE CASCADE
);

-- 7. Skincare routines
CREATE TABLE IF NOT EXISTS skincare_routines (
    routine_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    routine_type ENUM('AM', 'PM') NOT NULL,
    routine_name VARCHAR(150),
    routine_steps TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE
);

-- 8. Admins
CREATE TABLE IF NOT EXISTS admins (
    admin_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
