const express = require('express');
const cors = require('cors');

const app = express();

app.use(express.json());
// Enable CORS for all requests
app.use(cors());

// Import routes
const authRoutes = require('./routes/auth');

// Use routes
app.use('/api/user', authRoutes);

const swaggerUi = require('swagger-ui-express');
const YAML = require('yamljs');
const swaggerDocument = YAML.load('./api-doc.yaml');

app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));


// Start the server
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`Server running on port ${PORT}`));

