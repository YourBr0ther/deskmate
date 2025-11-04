# Multi-stage build for React frontend
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --only=production

# Copy source code
COPY . .

# Build the app
RUN npm run build

# Production stage with nginx
FROM nginx:alpine as production

# Create non-root user
RUN addgroup -g 1000 -S deskmate && \
    adduser -u 1000 -D -S -G deskmate deskmate

# Create necessary directories with proper permissions
RUN mkdir -p /var/cache/nginx /var/run /var/log/nginx && \
    chown -R deskmate:deskmate /var/cache/nginx /var/run /var/log/nginx /usr/share/nginx/html && \
    touch /var/run/nginx.pid && \
    chown deskmate:deskmate /var/run/nginx.pid

# Copy built app to nginx
COPY --from=build --chown=deskmate:deskmate /app/build /usr/share/nginx/html

# Copy custom nginx config
COPY --chown=deskmate:deskmate nginx.conf /etc/nginx/conf.d/default.conf

# Switch to non-root user
USER deskmate

# Expose port 80
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]