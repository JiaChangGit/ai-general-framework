FROM node:22-slim
RUN npm i -g @colbymchenry/codegraph@1.6.4 && codegraph version > /versions.txt 2>&1
