FROM node:22-slim
RUN npm i -g codebase-memory-mcp && (npm ls -g codebase-memory-mcp; codebase-memory-mcp --version) > /versions.txt 2>&1; cat /versions.txt
