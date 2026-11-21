# 音樂與音訊

作曲、編曲、歌詞、記譜、歌聲與語音合成、音訊處理，分三類：純文字的創作輔助 skill（music-composition-skills，不產生音訊、不外送）；雲端生成 API（Beatra、TinyMusic，背後是 Suno 等，要帳號與點數，使用權看條款）；本機開源模型（ACE-Step、YuE、MusicGen，這台沒有 GPU，都不實用）。

模型權重的授權要另外看：YuE 與 MusicGen 的權重是非商業授權。符號音樂用 music21 驗證和弦與音域，譜面用 LilyPond 或 ABC 記譜：AI 寫文字，工具渲染。

<!-- ecosystem:table ai-music -->
| 名稱 | 類型 | Tier | 授權 | 最後更新 | 證據 | 說明 |
|---|---|---|---|---|---|---|
| [music-composition-skills（jtydhr88）](https://github.com/jtydhr88/music-composition-skills) | skill 集 | 1 | 有條件（MIT） | 2026-10-30 | 讀原始碼 | 29 個 Claude Code／Codex skill，依 50 本編曲與音樂書籍整理成流程，輸出 ARR-SPEC（key、tempo、逐小節段落圖、和弦、誰何時進出、能量曲線）；不產生音訊。 |
| [Kokoro（Kokoro-82M／kokoro-onnx）](https://github.com/thewh1teagle/kokoro-onnx) | 函式庫 | 2 | 可使用（MIT（kokoro-onnx）；模型權重 Apache-2.0（Hugging Face 模型卡 hexgrad/Kokoro-82M）） | 2026-09-01 | 只有搜尋摘要 | 82M 參數的開放權重 TTS；kokoro-onnx 提供輕量 ONNX 推論，Stickman Kino 用它做本機旁白。 |
| [lyrics-to-song-skill（Beatra）](https://github.com/beatra-ai/lyrics-to-song-skill) | skill | 2 | 有條件（MIT-0） | 2026-11-20 | 讀原始碼 | 把完整歌詞、草稿或 hook 整理成有段落、風格與唱腔指示的歌曲請求，經 Beatra 以 Suno 6／MiniMax Music 3.0 渲染成音檔。 |
| [music21](https://github.com/cuthbertLab/music21) | 函式庫 | 2 | 可使用（BSD-3-Clause） | 2026-11-18 | 只有搜尋摘要 | MIT 開發的 Python 音樂分析與符號音樂工具包：讀寫 MusicXML、MIDI、ABC、和聲分析、輸出譜。 |
| [ABC notation（abcjs、abc2midi）](https://github.com/paulrosen/abcjs) | 函式庫 | 3 | 需人工確認（MIT（abcjs；GitHub 回報 NOASSERTION，需核對）） | 2026-11-18 | 只有搜尋摘要 | ABC 是文字記譜格式；abcjs 在瀏覽器渲染與播放，abc2midi（abcMIDI）轉成 MIDI。 |
| [ACE-Step（1.5）](https://github.com/ace-step/ACE-Step-1.5) | 專案 | 3 | 需人工確認（MIT（專案程式碼）；舊版 ACE-Step 1.0 倉庫為 Apache-2.0） | 2026-11-08 | 讀文件 | 開源音樂生成基礎模型：文字加歌詞生成含人聲歌曲，1.5 版 README 自稱品質介於 Suno v4.5 與 v5 之間（作者自報）；可 LoRA 訓練。 |
| [DiffSinger（openvpi）](https://github.com/openvpi/DiffSinger) | 專案 | 3 | 有條件（Apache-2.0） | 2026-11-19 | 讀文件 | 歌聲合成：輸入樂譜與歌詞，用擴散模型輸出歌聲；社群重構版，面向 OpenUtau 等製作流程。 |
| [LilyPond](https://github.com/lilypond/lilypond) | CLI | 3 | 需人工確認（GPL-3.0） | 2026-11-21 | 只有搜尋摘要 | 文字描述樂譜、輸出排版精美的 PDF／SVG／MIDI。 |
| [MuseScore（命令列轉檔）](https://github.com/musescore/MuseScore) | CLI | 3 | 需人工確認（GPL-3.0（通識；GitHub 回報 NOASSERTION）） | 2026-11-20 | 只有搜尋摘要 | 開源記譜軟體；可用命令列轉檔 MusicXML、MIDI、PDF、PNG、音訊。 |
| [Piper（rhasspy → OHF-Voice/piper1-gpl）](https://github.com/OHF-Voice/piper1-gpl) | CLI | 3 | 有條件（GPL-3.0（piper1-gpl）；舊 rhasspy/piper 為 MIT） | 2026-11-20 | 只有搜尋摘要 | 快速、可純 CPU 的本機神經 TTS。原 rhasspy/piper 已封存（2025-08-26），維護轉到 OHF-Voice/piper1-gpl（GPL-3.0）。 |
| [TinyMusic agent skills](https://github.com/TinyMusicAI/tinymusic-agent-skills) | skill 集 | 3 | 有條件（MIT） | 2026-10-20 | 讀原始碼 | 6 個免費 skill（歌曲、歌詞、風格提示詞、免版稅 BGM、禮物歌、品牌 jingle），預設只產生可貼到 TinyMusic 網站的生成包；接上選配 MCP 才直接生成。 |
| [AudioCraft（MusicGen／AudioGen）](https://github.com/facebookresearch/audiocraft) | 函式庫 | 4 | 不建議（MIT（程式碼）；模型權重 CC-BY-NC 4.0） | 2026-03-03 | 讀文件 | Meta 的音訊生成函式庫，含 MusicGen 文字轉音樂、EnCodec。 |
| [OpenUtau](https://github.com/stakira/OpenUtau) | 應用 | 4 | 有條件（MIT） | 2026-11-16 | 只有搜尋摘要 | 開源歌聲合成編輯器（.NET，跨平台，GUI），支援 DiffSinger、ENUNU 等多種歌手。 |
| [SoX](https://sourceforge.net/projects/sox/) | CLI | 4 | 需人工確認（GPL-2.0-or-later／LGPL-2.1（依元件）） | — | 只有搜尋摘要 | 音訊處理的瑞士刀：轉格式、剪裁、混音、淡入淡出、取樣率轉換、頻譜圖。 |
| [YuE（YuE2）](https://github.com/multimodal-art-projection/YuE) | 專案 | 4 | 不建議（Apache-2.0（程式碼）；模型權重 CC BY-NC 4.0 加附加創作者許可） | 2026-11-01 | 讀文件 | 開放歌詞轉歌曲模型，YuE2 輸出 48 kHz 立體聲；README 自稱在 WildSongBench 上與 Suno v5／v6 相當（作者自報）。 |
<!-- /ecosystem -->
