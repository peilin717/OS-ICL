# OS ICL 三十六题评分与演示接口

新版入口为 `/studio36`，沿用当前 OS 桌面与九个应用。任务编号为 OS-E-01 至 OS-E-12、OS-M-01 至 OS-M-12、OS-H-01 至 OS-H-12。

## 创建人工试做或评测实例

```bash
curl http://127.0.0.1:8790/api/v2/sessions \
  -H 'Content-Type: application/json' \
  -d '{"case_id":"OS-E-01","mode":"evaluation","convention":0,"seed":4201}'
```

把返回的 `launch_url` 接到服务地址后，在浏览器中打开。`convention` 为 0/1/2，分别对应 A/B/C；它由可信控制端选择，不提供给被评测模型。任务说明与初始业务材料会一起生成。

## 判定当前状态

```bash
curl http://127.0.0.1:8790/api/v2/sessions/SESSION_ID/judge \
  -H 'Content-Type: application/json' -d '{}'
```

返回示例：

```json
{
  "session_id": "osl_...",
  "status": "active",
  "result": {
    "success": false,
    "goal_success": false,
    "rule_compliance": false,
    "side_effect_free": true,
    "failed_checks": ["result.000"],
    "scope": "query",
    "judge_version": 1
  }
}
```

`success` 是全部必要结果与保护条件的合取。judge 读取服务器保存的当前实例，不接受调用者提交的 state、expected 或 success。它不结束任务、不清空操作，也不修改结果状态。`checks` 与 `failed_checks` 用于诊断；`partial_credit` 包含保护条件，不能直接当作业务完成百分比。

该接口属于可信控制端，不应作为视觉模型可反复调用的提示工具。模型仍只使用视频、截图和鼠标键盘。

## 结束与重置

```bash
curl http://127.0.0.1:8790/api/v2/sessions/SESSION_ID/finish \
  -H 'Content-Type: application/json' -d '{}'

curl http://127.0.0.1:8790/api/v2/sessions/SESSION_ID/reset \
  -H 'Content-Type: application/json' -d '{}'
```

finish 使用与 judge 相同的评分器，并结束本次实例。reset 恢复其原始材料和状态，清除操作、录像状态与结果。

## 局部规则演示

创建时使用 `mode: "demo"`。对于这 36 题，服务会创建独立的局部方法示范，而非完整 query 的解题录像。作者可在开始前查看方法说明；开始后恢复普通桌面，通过 Start → Finish recording 结束。

演示结果中的 `scope` 是 `demo`；它通过仅表示局部方法正确，不表示对应长程 query 已完成。演示和 query 使用不同的实例结构及独立状态。

录制脚本 `scripts/record36_coordinates.py` 使用浏览器截图、坐标鼠标及键盘输入。作者预先知道规则和材料，读取可信状态仅核对输入是否实际生效，不向在线实例发送语义动作。来源标记为 `oracle-assisted-coordinate-ui`，不是人工录像或独立视觉模型基线。

现有录制器记录实际交互，再从初始状态回放生成 1280×720 WebM，要求最终状态哈希一致。完整逐时间线视觉审阅仍是单独步骤。

## 目录与适用范围

- `GET /api/v2/cases?catalogue=36`：新版 36 题目录。
- `/studio36`：新版任务创建和录制入口。
- `/studio`：同样使用新版 36 题，旧任务不再对外开放。
- `tasks36.py`：初始材料、任务目标、独立局部示范与可信参考操作。
- `judge36.py`：实际状态判据、内容/来源/依赖验证及保护集。
- `scripts/package36_recordings.py`：只打包当前源码、judge 成功且回放已验证的录像。

当前为 `36.1-dev` 目录。任务夹具和评分已接入；最终验收还需要完整 query 的普通浏览器执行、完整视频视觉审核及独立模型评测，不能仅凭引擎测试或局部示范声称全部验收通过。

## 视频存储位置（2026-10-16）

原始录像位于 `/root/VideoICL-bench/OS-ICL/data/videos/`，录制检查点和截图位于 `data/task36-release/`。最终合集默认输出到 `/root/VideoICL-bench/OS-ICL/data/demo36/`（含 `index.html`、`manifest.json` 和 `videos/`）。视频不输出到 C 盘；打包脚本拒绝 `/mnt/c/` 目标。Windows 可通过 `\\wsl.localhost\Ubuntu\root\VideoICL-bench\OS-ICL\data\` 访问。
