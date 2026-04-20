# macos-uninstall-inspector

**削除する前に、そのアプリが本当に何を持っているかを知る。**

`macos-uninstall-inspector` は、macOS アプリのアンインストール候補を **削除前に** 調べ、

- **何を消すべきか**
- **なぜそれが候補なのか**
- **どれくらい確からしいのか**

を説明する provenance-aware な read-only inspector です。

単に `.app` の名前に引っかかったファイルを集めるのではなく、まず配布経路や構造化された証拠を見ます。

- **Homebrew** で入ったのか
- **pkg** と receipt/BOM があるのか
- **Mac App Store** アプリか
- **Setapp 管理** か
- **Adobe のような vendor-managed suite** か
- そのパスは **app-owned** か **vendor-shared** か **heuristic-only** か

## なぜ作るのか

従来の Mac 用アンインストール系ツールは、「それっぽい残骸」を集めることは得意でも、**所有関係の説明** が弱いことがあります。

このリポジトリはそこを重視します。

- 名前一致より先に structured provenance
- 断定ではなく confidence score
- `safe` / `balanced` / `aggressive` の段階的レビュー
- vendor 対応は重要だが、個別ハックの山ではなく再利用可能な一般則を優先

`sudo` は **見える範囲** や **削除権限** を広げますが、
**そのファイルが本当にそのアプリ専用かどうか** は別問題です。

## 現在できること

実装済み:
- read-only CLI: `mui inspect <App.app>`
- Homebrew / pkg の runtime context 収集
- app bundle からの identity 抽出
- distribution 判定
  - plain / MAS / Homebrew / pkg / Setapp / Adobe vendor-suite
- embedded helper と一般的な `~/Library` 領域の scan
- evidence score / ownership class の算出
- `safe` / `balanced` / `aggressive` mode filter
- `schemas/finding.schema.json` に対する JSON validation

未実装 / 今後:
- `LaunchAgents` / `LaunchDaemons` / `PrivilegedHelperTools` の深掘り
- entitlements / group containers / UUID container metadata の相関
- Adobe 以外の vendor adapter 拡張
- review 前提の delete engine

## 中核の考え方

探索は **使える手法を全部試す** べきですが、すべてを同格には扱いません。

### 証拠の優先順

1. **Distribution provenance**
   - Homebrew cask metadata / zap / uninstall artifacts
   - pkg receipts + BOMs
   - MAS receipt / App Store metadata
   - Setapp-managed markers
   - official uninstaller / cleaner
2. **Bundle に埋め込まれた component**
   - `Contents/Library/LoginItems`
   - `Contents/Library/SystemExtensions`
   - `Contents/Helpers`
   - `Contents/XPCServices`
   - `Contents/PlugIns`
3. **Entitlements / containers**
   - app groups
   - sandbox containers
   - `containermanagerd` metadata
4. **System integration assets**
   - LaunchAgents / LaunchDaemons
   - PrivilegedHelperTools
   - audio plug-ins
   - QuickLook / PreferencePanes / Internet Plug-Ins / widgets など
5. **User-space state**
   - Application Support
   - Caches
   - Preferences
   - Logs
   - Saved Application State
   - WebKit / HTTPStorages
6. **Heuristic fallback**
   - Spotlight
   - path/name/vendor matching
   - stripped app names
   - team identifier / vendor hints

## ベンダ個別最適より、汎用公式を重視

このプロジェクトでは、vendor ごとの場当たり対応よりも、**複数 vendor に再利用できる一般則** を大切にします。

目指すのは、vendor ごとに別実装を増やし続けることではなく、例えば次のような公式です。

- official manager を先、generic fallback を後
- structured provenance を先、heuristic fallback を後
- `app-owned` と `vendor-shared` を分離
- system integration を明示的に分類
- すべての candidate に evidence と confidence を付ける

vendor adapter は必要ですが、それは「個別最適そのもの」ではなく、**再利用可能な policy pattern を表現するためのもの** であるべきです。

詳細は [`docs/generic-vendor-formulas.md`](docs/generic-vendor-formulas.md) を参照してください。

## 対応クラス

### Generic
- DMG / ZIP / plain app bundles
- MAS apps
- 多くの pkg-installed apps

### Managed distribution
- Homebrew casks
- Setapp apps

### Vendor-managed suites
- Adobe Creative Cloud 系
- 将来的には Microsoft Office / Autodesk / JetBrains Toolbox / Steam など

## Safety model

このリポジトリは **deleter ではなく inspector** です。

将来的な削除エンジンも、まずは:
- candidate を evidence / confidence 付きで出す
- `vendor-shared` を分離する
- レビューを前提にする
- Adobe / Setapp / Homebrew / pkg は正しい manager を先に通す

という方針です。

## Quick start

```bash
cd macos-uninstall-inspector
python3 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest -q
python scripts/validate_examples.py
mui inspect /Applications/Claude.app
mui inspect /Applications/Claude.app --mode safe
```

## 出力例

```bash
mui inspect /Applications/Claude.app --mode safe
```

JSON で次を返します。
- app identity
- distribution kind
- mode thresholds
- candidate paths
- ownership class
- score
- evidence
- warnings
- included modes

## リポジトリ内容

- `docs/architecture.md` — 全体設計
- `docs/pipeline.md` — 探索順序
- `docs/distribution-strategies.md` — Homebrew / pkg / MAS / Setapp / Adobe の扱い
- `docs/confidence-model.md` — score と candidate 分類
- `docs/roadmap.md` — 実装ロードマップ
- `docs/generic-vendor-formulas.md` — vendor handling の一般則
- `schemas/finding.schema.json` — inspection result の JSON schema
- `examples/` — サンプル出力
- `scripts/validate_examples.py` — schema validation helper
- `tests/` — schema と inspector 挙動のテスト

## 初期スコープ

この公開リポジトリは、詳細設計に加えて read-only MVP inspector まで含んでいます。

## License

MIT
