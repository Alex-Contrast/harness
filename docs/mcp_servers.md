https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
https://github.com/modelcontextprotocol/servers/tree/main/src/git
https://github.com/modelcontextprotocol/servers/tree/main/src/memory
https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking
https://github.com/modelcontextprotocol/servers/tree/main/src/time
https://github.com/github/github-mcp-server
https://github.com/nickclyde/duckduckgo-mcp-server

2 separate issues:

1. NPM Auth Error
   npm ERR! code E401
   npm ERR! Incorrect or missing password.
   Your npm is configured to authenticate somewhere but the credentials are stale/wrong. Fix:
   npm logout
# or check ~/.npmrc for any registry auth configs

2. uvx TLS Certificate Error
   invalid peer certificate: UnknownIssuer
   Your Python/uvx isn't trusting system SSL certs. Common on macOS with pyenv. Fix:
# Option 1: Use native TLS
export UV_NATIVE_TLS=1

# Option 2: Install certifi and point to it
pip install certifi
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")

Want to try fixing one of these, or should I add back the custom tools as fallback so harness works regardless?
