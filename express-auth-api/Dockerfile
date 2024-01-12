# Use the official Node.js 16 image as a parent image
FROM node:16

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the package.json and package-lock.json files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of your application's code
COPY . .

# Your application's default port, change if different
EXPOSE 3000

# The command to run your application
CMD [ "npm", "start" ]
