# Vercel Deployment Guide

This is a **Python project**. You don't need Node.js or npm to deploy it!

## Project Structure

```
movies-mcp-server/
├── api/
│   └── index.py          # Vercel serverless function handler
├── main.py               # Local development server
├── local_test_client.py  # Test client for local development
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
├── mcp_manifest.json    # MCP tool manifest
├── .vercelignore        # Files to exclude from deployment
└── .env                 # Local environment variables (not deployed)
```

## Prerequisites

1. A Vercel account (sign up at https://vercel.com)
2. A GitHub account (for easiest deployment method)

## Environment Variables

You need to configure these environment variables in Vercel:

1. `AUTH0_DOMAIN` - Your Auth0 domain (e.g., `movies-demo.us.auth0.com`)
2. `AUTH0_CLIENT_ID` - Your Auth0 M2M client ID
3. `AUTH0_CLIENT_SECRET` - Your Auth0 M2M client secret
4. `AUTH0_AUDIENCE` - Your Auth0 API identifier (e.g., `https://movies.example.com`)
5. `NODE_API_URL` - Your Node.js backend API URL (production URL, not localhost)

## Deployment Methods

### Method 1: GitHub Integration (Recommended - No CLI needed!)

This is the easiest method and requires no additional tools.

1. **Push your code to GitHub**:
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Connect to Vercel**:
   - Go to https://vercel.com/dashboard
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will auto-detect it's a Python project

3. **Configure Environment Variables**:
   - During import, or after in Project Settings → Environment Variables
   - Add all 5 environment variables listed above
   - Make sure to add them for Production environment

4. **Deploy**:
   - Click "Deploy"
   - Vercel will build and deploy automatically
   - Future pushes to main branch will auto-deploy

### Method 2: Vercel Dashboard (Manual Upload)

If you don't want to use GitHub:

1. **Prepare your project**:
   - Make sure all files are ready
   - Ensure `.vercelignore` excludes unnecessary files

2. **Upload via Dashboard**:
   - Go to https://vercel.com/dashboard
   - Click "Add New Project"
   - Choose "Upload" option
   - Drag and drop your project folder (or select files)

3. **Configure Environment Variables**:
   - In Project Settings → Environment Variables
   - Add all 5 variables before deploying

4. **Deploy**:
   - Click "Deploy"

### Method 3: Vercel CLI (Optional)

Only use this if you prefer command-line deployment. Note: Vercel's CLI is distributed via npm (Node.js package manager), but this doesn't affect your Python project - it's just how Vercel chose to distribute their CLI tool.

1. **Install Vercel CLI** (requires Node.js):
   ```bash
   npm install -g vercel
   ```

2. **Login and Deploy**:
   ```bash
   vercel login
   vercel --prod
   ```

3. **Set Environment Variables**:
   ```bash
   vercel env add AUTH0_DOMAIN
   vercel env add AUTH0_CLIENT_ID
   vercel env add AUTH0_CLIENT_SECRET
   vercel env add AUTH0_AUDIENCE
   vercel env add NODE_API_URL
   ```

## Setting Environment Variables via Dashboard

1. Go to your project on Vercel
2. Click "Settings" → "Environment Variables"
3. For each variable:
   - Enter the name (e.g., `AUTH0_DOMAIN`)
   - Enter the value (e.g., `movies-demo.us.auth0.com`)
   - Select environments: Production, Preview, Development
   - Click "Save"

## Testing Your Deployment

After deployment, test your MCP server with curl:

```bash
curl -X POST https://your-deployment-url.vercel.app \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "search_movies",
      "arguments": {
        "query": "The Matrix"
      }
    }
  }'
```

Or test with Python:

```python
import requests

response = requests.post(
    "https://your-deployment-url.vercel.app",
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_movies",
            "arguments": {"query": "The Matrix"}
        }
    }
)

print(response.json())
```

## Local Development

To test locally before deploying:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run local server
python main.py

# In another terminal, test with the client
python local_test_client.py
```

## Important Notes

1. **Serverless Function Limits**:
   - Vercel Hobby: 10 second timeout
   - Vercel Pro: 60 second timeout
   - Ensure your API calls complete within these limits

2. **Cold Starts**:
   - Serverless functions may experience cold starts
   - First request might be 1-2 seconds slower

3. **Environment Variables**:
   - Never commit `.env` file to git
   - Always use Vercel's environment variable system for production
   - The `.env` file is already in `.gitignore`

4. **Node API URL**:
   - Must point to your production Node.js API
   - Cannot use `localhost` in production
   - Update `NODE_API_URL` environment variable accordingly

5. **Python Version**:
   - Vercel uses Python 3.9 by default
   - Your code should be compatible with Python 3.9+

## Troubleshooting

### Deployment Fails
- Check the build logs in Vercel dashboard
- Verify all dependencies are in `requirements.txt`
- Ensure Python version compatibility
- Check that `api/index.py` exists and is valid

### Function Timeout
- Optimize your Auth0 token requests
- Consider implementing token caching with expiration
- Optimize the Node.js API calls
- Upgrade to Vercel Pro for longer timeouts

### Environment Variables Not Working
- Verify variables are set in Vercel dashboard
- Check that variable names match exactly (case-sensitive)
- Redeploy after adding new variables
- Make sure variables are set for the correct environment

### 404 or 500 Errors
- Check deployment logs for errors
- Verify `vercel.json` routing configuration
- Test the endpoint with curl to see actual error
- Check that all imports are in `requirements.txt`

## Updating Your Deployment

### With GitHub Integration (Automatic)
```bash
# Make your code changes
git add .
git commit -m "Update feature X"
git push origin main
# Vercel will automatically deploy
```

### Manual Update
- Re-upload your project via dashboard, or
- Run `vercel --prod` if using CLI

## Monitoring

Monitor your deployment in the Vercel Dashboard:
- **Logs**: Real-time function execution logs
- **Analytics**: Request counts and performance
- **Deployments**: History of all deployments
- **Issues**: Automatic error tracking

## Security Best Practices

1. **Secrets**: Use Vercel environment variables for all secrets
2. **CORS**: Configure if needed (add to `vercel.json`)
3. **Rate Limiting**: Consider implementing if API is public
4. **Monitoring**: Set up alerts for unusual activity
5. **Credentials**: Regularly rotate Auth0 credentials
6. **HTTPS**: All Vercel deployments use HTTPS by default

## Getting Your Deployment URL

After deploying, your MCP server will be available at:
- Production: `https://your-project-name.vercel.app`
- Preview: `https://your-project-name-git-branch.vercel.app`

You can find the exact URL in:
- Vercel Dashboard → Your Project → Deployments
- Or in the deployment confirmation output
