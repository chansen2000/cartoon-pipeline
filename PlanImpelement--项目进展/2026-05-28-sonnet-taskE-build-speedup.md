# Sonnet Task E — build_assets.sh 提速 + cmake 块清爽化

**日期**: 2026-05-28
**状态**: ✅ 完成

## 改动

| 文件 | 操作 | 说明 |
|------|------|------|
| `build_assets.sh` | 修改 | 顶部加 --fast 旗标解析；[1]-[8] 包 if FAST_MODE=0；[9] 拆 [9a] 资产(fast跳过)+[9b] INI(始终)；cmake 块 CMakeCache.txt 判定；Done 提示 fast 简化 |

## 验证结果

| # | 项 | 结果 |
|---|-----|------|
| 1 | git diff | ✅ 仅预期改动 |
| 2 | 全量 build | ✅ 5m22s |
| 3 | fast 模式启动 | ✅ 日志 `[FAST]`, 跳过 [1]~[8] |
| 4 | fast 耗时 | ✅ 3.36s < 5s |
| 5-8 | INI 改值 fast 验证 | ✅ hat_dx 变更正确嵌入 + bin/main 刷新 |
| 9 | --bogus | ✅ exit 1 |
| 10 | CMakeCache.txt 删后重 cmake | ✅ 自动重建 |

## sheng 工作流

- 调 INI → `bash build_assets.sh --fast` → 3s 反馈
- 资源更新 → `bash build_assets.sh` → 全量

## git

- commit: `cae851f` — Task E: --fast flag + cmake block cleanup
- push: ✅ main → origin/main
