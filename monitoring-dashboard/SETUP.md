# Quick Setup Guide

## Step 1: Install Dependencies

```bash
cd monitoring-dashboard
npm install
```

## Step 2: Ensure Server is Running

Make sure the monitoring server is running on port 5000:

```bash
cd ../monitoring-server
npm run dev
```

## Step 3: Start the Dashboard

```bash
cd ../monitoring-dashboard
npm run dev
```

## Step 4: Access the Dashboard

Open your browser and navigate to:
```
http://localhost:3000
```

## Step 5: Login

Use the default credentials:
- Username: `admin`
- Password: `admin123`

## Troubleshooting

### Port Already in Use

If port 3000 is already in use, you can change it in `vite.config.ts`:

```typescript
server: {
  port: 3001, // Change to any available port
  // ...
}
```

### API Connection Issues

1. Verify the server is running on port 5000
2. Check the proxy configuration in `vite.config.ts`
3. Ensure no firewall is blocking the connection

### Build Errors

If you encounter build errors:

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf node_modules/.vite
```

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to your code will reflect immediately in the browser without a full reload.

### TypeScript Errors

Run TypeScript check:
```bash
npm run build
```

### Linting

Run ESLint:
```bash
npm run lint
```

## Production Deployment

### Build

```bash
npm run build
```

### Preview Build

```bash
npm run preview
```

### Deploy

The `dist` folder contains the production build. Deploy it to any static hosting service:

- Vercel
- Netlify
- AWS S3 + CloudFront
- GitHub Pages
- Any web server (nginx, Apache, etc.)

### Environment Variables

For production, update the API URL in your hosting platform's environment variables or create a `.env.production` file:

```
VITE_API_URL=https://your-api-domain.com/api
VITE_WS_URL=wss://your-api-domain.com/ws
```

## Features to Explore

1. **Dashboard** - Overview of all employees and statistics
2. **Employees** - Detailed list with search functionality
3. **Employee Details** - Individual activity tracking and charts
4. **Screenshots** - Gallery view of captured screenshots
5. **Theme Toggle** - Switch between light and dark modes
6. **Real-time Updates** - WebSocket connection for live data

Enjoy monitoring! 🚀


## Remote Configuration Management ⭐ NEW

The dashboard now includes a powerful remote configuration feature that allows you to manage client settings from the web interface.

### Accessing Configuration Settings

1. Login to the dashboard
2. Navigate to **Settings** (gear icon in sidebar)
3. Click on the **Configuration** tab
4. Select an employee from the dropdown

### Available Settings

#### Interval Settings
- **Screenshot Interval**: How often to capture screenshots (default: 10 min)
- **App Switch Capture Delay**: Delay after switching applications (default: 5 sec)
- **Idle Threshold**: Time before marking user as idle (default: 5 min / 300 sec)
- **Data Send Interval**: How often to transmit data to server (default: 10 min)

#### Screenshot Settings
- **Screenshot Quality**: JPEG compression quality from 1-100 (default: 75)
  - Lower values = smaller files, lower quality
  - Higher values = larger files, better quality

#### File Transfer Settings
- **Download Path**: Directory where clients save OTA files
- **Sync Interval**: How often to check for new files (default: 30 sec)

#### Advanced Settings
- **Log Level**: Client logging verbosity (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **Server URL**: API endpoint for the client
- **Location Update Interval**: How often to update GPS/IP location (default: 30 min)

### How Configuration Updates Work

1. **Edit Settings**: Adjust any configuration parameter in the UI
2. **Save Changes**: Click the "Save Changes" button
3. **Automatic Detection**: Client checks for updates every 60 seconds
4. **Auto-Restart**: Client automatically restarts to apply new settings
5. **Confirmation**: Success message appears when configuration is saved

### Configuration Update Flow

```
Dashboard UI → Server API → Database → Client Detection → Client Restart
```

The entire process is automatic and requires no manual intervention on the client side.

### Best Practices

1. **Test First**: Test configuration changes on a single client before rolling out to all
2. **Reasonable Values**: Use the recommended values as guidelines
3. **Monitor Impact**: Watch client behavior after configuration changes
4. **Document Changes**: Keep notes on why configurations were changed

### Troubleshooting Configuration

**Client not detecting changes:**
- Wait at least 60 seconds for the client to check for updates
- Verify the client is online and connected to the server
- Check client logs for config watcher errors

**Configuration not applied:**
- Ensure the client restarted successfully
- Check the client's `.env` file was updated
- Review client logs for configuration loading errors

**Version mismatch:**
- Check the database for the correct version number
- Verify the client is checking the correct API endpoint

For technical details, see [REMOTE_CONFIG.md](../monitoring-server/REMOTE_CONFIG.md).

