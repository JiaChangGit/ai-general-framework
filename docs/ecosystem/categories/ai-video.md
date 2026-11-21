# 影片與動畫

<!-- ecosystem:table ai-video -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [Remotion](https://github.com/remotion-dev/remotion) | 函式庫 | 1 | 有條件（Remotion License（自訂）） | 2026-11-20 | 讀原始碼 | 用 React 寫影片：程式化的場景與動畫，由 Chrome 逐格渲染，ffmpeg 編碼成 MP4；含 Studio 預覽、CLI、Lambda、字幕與 Whisper 整合、以及一組 agent skills。 |
| [Stickman Kino（dsauce）](https://github.com/dsauce/stickman-kino) | skill 集 | 1 | 可使用（MIT） | 2026-10-08 | 讀原始碼 | 由 coding agent 導演、以程式碼渲染的火柴人影片：agent 寫 film.json 與 scenes.js，本機 Kokoro 旁白與合成音樂，HyperFrames 逐格渲染成 MP4；不用任何影片生成模型或 API。 |
| [claude-animated-shorts（mromidev）](https://github.com/mromidev/claude-animated-shorts) | skill | 2 | 有條件（MIT） | 2026-11-01 | 讀原始碼 | 一個 Claude skill（cartoon-3d-short）：用 three.js 與 Remotion 做 55～70 秒直式 2D 角色加 3D 世界的動畫短片；流程為題材與事實、腳本、旁白、story.ts 鏡頭表、靜態影格、渲染、QA。 |
| [FFmpeg](https://github.com/FFmpeg/FFmpeg) | CLI | 2 | 有條件（LGPL-2.1-or-later／GPL-2.0-or-later（依編譯選項；GitHub 回報 NOASSERTION）） | 2026-11-21 | 只有搜尋摘要 | 音訊與影片的轉碼、剪輯、擷取影格、混音、字幕燒錄與串流的標準工具。 |
| [HyperFrames（HeyGen）](https://github.com/heygen-com/hyperframes) | 函式庫 | 2 | 可使用（Apache-2.0） | 2026-11-21 | 讀文件 | 把 HTML＋GSAP 暫停時間軸在 headless Chrome 逐格 seek 渲染成影片的框架（Stickman Kino 的渲染底層）。 |
| [Manim（Community Edition）](https://github.com/ManimCommunity/manim) | 函式庫 | 2 | 可使用（MIT） | 2026-11-21 | 只有搜尋摘要 | 3Blue1Brown 風格的數學與演算法動畫，Python 場景類別，輸出 MP4／GIF。 |
| [Motion Canvas](https://github.com/motion-canvas/motion-canvas) | 函式庫 | 3 | 可使用（MIT） | 2026-07-02 | 只有搜尋摘要 | 用 TypeScript generator 函式寫向量動畫並在編輯器預覽、匯出影片的工具，偏講解類動畫。 |
| [Revideo](https://github.com/midrender/revideo) | 函式庫 | 3 | 可使用（MIT） | 2026-07-15 | 只有搜尋摘要 | Motion Canvas 的分支，提供可程式化的影片渲染 API（renderVideo）與 Player，面向應用程式內產生影片。 |
<!-- /ecosystem -->
