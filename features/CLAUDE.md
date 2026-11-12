# features/ 規則

- 這裡的 `.feature` 檔是唯一的行為規格。
- **只有主 session 能修改**，而且要先得到使用者在對話中明確同意。implementer、verifier、runner 只能讀。
- 結構：`features/<模組>/<行為>.feature`，模組名稱對應 `docs/ARCHITECTURE.md`。
- 撰寫方式、標籤定義與範本：`bdd-spec` skill。
- 修改已核准 feature 的規則：見 `bdd-spec` skill 流程第 5 步。
