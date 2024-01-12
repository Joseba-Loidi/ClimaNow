const express = require('express');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const mysql = require('mysql2/promise');
const router = express.Router();

// Configura la conexión a la base de datos MySQL
const pool = mysql.createPool({
    host: 'localhost',
    user: 'root',
    password: 'root',
    database: 'ClimaNow',
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});
// Agrega la declaración de consola para verificar la conexión
console.log('Conexión a la base de datos establecida correctamente');

let revokedTokens = [];
// Register user
router.post('/register', async (req, res) => {
    const { username, password, mail } = req.body;
    
    // Verifica que los valores necesarios no sean undefined
    if (!username || !password || !mail) {
        return res.status(400).send('Username, password, and mail are required');
    }

    try {
        // Verifica si el usuario ya está registrado
        const [existingUserRows, existingUserFields] = await pool.execute(
            'SELECT * FROM users WHERE username = ? OR mail = ?',
            [username, mail]
        );
        if (existingUserRows.length > 0) {
            // El usuario o el correo ya están registrados
            console.log('Username or mail already registered')
            return res.status(400).send('Username or mail already registered');
        }

        const hashedPassword = await bcrypt.hash(password, 10);

        // Inserta el usuario en la base de datos
        const [insertedUserRows, insertedUserFields] = await pool.execute(
            'INSERT INTO users (username, password, mail) VALUES (?, ?, ?)',
            [username, hashedPassword, mail]
        );

        console.log(`User ${username} registered successfully`);
        res.status(201).send('User registered successfully');
    } catch (error) {
        console.error('Error registering user:', error);
        res.status(500).send('Internal Server Error');
    }
});


// Login user
router.post('/login', async (req, res) => {
    const { username, password } = req.body;
    const [rows, fields] = await pool.execute(
        'SELECT * FROM users WHERE username = ?',
        [username]
    );

    const user = rows[0];
    if (user && await bcrypt.compare(password, user.password)) {
        const token = jwt.sign({ username: user.username }, 'secret');
        // Almacena el token en la base de datos
        await pool.execute(
            'UPDATE users SET jwt = ? WHERE username = ?',
            [token, username]
        );
        console.log(`User ${user.username} logged successfully`);
        res.json({ token });
    } else {
        console.log("Invalid credentials");
        res.status(400).send('Invalid credentials');
    }
});

/// Logout user (revoca el token)
router.post('/logout', async (req, res) => {
    const { token } = req.body;
    // Borra el token en la base de datos al realizar el logout
    await pool.execute(
        'UPDATE users SET jwt = NULL WHERE jwt = ?',
        [token]
    );
    console.log(`User logged out successfully`);
    res.json({ message: 'Logout successful' });
});


// Nuevo endpoint para obtener datos del usuario
router.post('/user-profile', async (req, res) => {
    const { token } = req.body;

    // Verifica si el token está presente en la solicitud
    if (!token) {
        return res.status(401).json({ message: 'Token missing' });
    }

    try {
        // Decodifica el token para obtener el nombre de usuario
        const payload = jwt.verify(token.replace('Bearer ', ''), 'secret');
        const username = payload.username;

        // Consulta la base de datos para obtener los datos del usuario
        const [rows, fields] = await pool.execute(
            'SELECT username, mail FROM users WHERE username = ?',
            [username]
        );

        // Verifica si se encontró al usuario en la base de datos
        if (rows.length === 0) {
            console.log(`User ${username}' not found`);
            return res.status(404).json({ message: 'User not found' });
        }

        // Obtiene los datos del usuario desde la base de datos
        const user = rows[0];
        console.log(`User ${username}'s profile retrieved successfully`);
        // Devuelve los datos del usuario
        res.json(user);
    } catch (error) {
        if (error instanceof jwt.TokenExpiredError) {
            return res.status(401).json({ message: 'Token has expired' });
        } else if (error instanceof jwt.JsonWebTokenError) {
            return res.status(401).json({ message: 'Invalid token' });
        } else {
            console.error('Error getting user profile:', error);
            res.status(500).send('Internal Server Error');
        }
    }
});
router.get('/get_favorites', async (req, res) => {
    const token = req.header('Authorization');

    // Verifica si el token está presente en el encabezado
    if (!token) {
        return res.status(401).json({ message: 'Token missing' });
    }

    try {
        // Extraer el token del encabezado
        const tokenParts = token.split(' ');
        if (tokenParts.length !== 2 || tokenParts[0] !== 'Bearer') {
            return res.status(401).json({ message: 'Invalid token format' });
        }

        const decodedToken = jwt.verify(tokenParts[1], 'secret');
        const username = decodedToken.username;

        // Obtén el ID del usuario
        const [userRows] = await pool.execute('SELECT id FROM users WHERE username = ?', [username]);
        const userId = userRows[0].id;

        // Obtener lista de ubicaciones favoritas
        const [favoritesRows] = await pool.execute('SELECT location FROM favorites WHERE user_id = ?', [userId]);
        const favorites = favoritesRows.map(row => row.location);
        if (favoritesRows.length === 0) {
            console.log(`User ${username} does not have any favorites`);
            return res.json({ favorites });
        }

        console.log(`Favorites retrieved successfully for user ${username}`);
        return res.json({ favorites });
    } catch (error) {
        console.error('Error getting favorites:', error);
        res.status(500).send('Internal Server Error');
    }
});

router.post('/add_favorites', async (req, res) => {
    
    const { token, location } = req.body;

    // Verifica si el token está presente en la solicitud
    if (!token) {
        return res.status(401).json({ message: 'Token missing' });
    }

    try {
        // Decodifica el token para obtener el nombre de usuario
        const payload = jwt.verify(token.replace('Bearer ', ''), 'secret');
        const username = payload.username;

        // Obtén el ID del usuario
        const [userRows] = await pool.execute('SELECT id FROM users WHERE username = ?', [username]);
        const userId = userRows[0].id;

        // Agregar ubicación a favoritos
        await pool.execute('INSERT INTO favorites (user_id, location) VALUES (?, ?)', [userId, location]);
        console.log(`Favorite added successfully for user ${username}`);
        res.json({ message: 'Favorite added successfully' });
    } catch (error) {
        console.error('Error adding favorite:', error);
        res.status(500).send('Internal Server Error');
    }
});
router.post('/delete_favorite', async (req, res) => {
    const { token, location } = req.body;
    
    // Verifica si el token está presente en la solicitud
    if (!token) {
        return res.status(401).json({ message: 'Token missing' });
    }

    try {
        // Decodifica el token para obtener el nombre de usuario
        const payload = jwt.verify(token.replace('Bearer ', ''), 'secret');
        const username = payload.username;

        // Obtén el ID del usuario
        const [userRows] = await pool.execute('SELECT id FROM users WHERE username = ?', [username]);
        const userId = userRows[0].id;

        // Eliminar ubicación de favoritos
        await pool.execute('DELETE FROM favorites WHERE user_id = ? AND location = ?', [userId, location]);
        console.log(`Favorite deleted successfully for user ${username}`);       
        res.json({ message: 'Favorite deleted successfully' });
    } catch (error) {
        console.error('Error deleting favorite:', error);
        res.status(500).send('Internal Server Error');
    }
});


module.exports = router;

