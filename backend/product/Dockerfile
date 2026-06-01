FROM node:latest

# Put code which need app to run in /app directory of container
WORKDIR /app

# envrionments and arguments
ENV AUTHAPP_PORT 3002

COPY . .

RUN npm install

EXPOSE 3002

CMD ["npm", "run", "start"]