# AUTOPS 编码规范

> 文档状态：current
> 建议路径：`docs/07-development/CODING_STYLE.md`

---

## 1. Python 后端

### 1.1 工具

- **格式化：** black（行宽 88）
- **Lint：** ruff
- **类型检查：** mypy --strict

### 1.2 命名

| 类型 | 风格 | 示例 |
|---|---|---|
| 模块 | snake_case | asset_service.py |
| 类 | PascalCase | AssetService |
| 函数/方法 | snake_case | get_asset_by_id |
| 常量 | UPPER_SNAKE | MAX_RETRY_COUNT |
| 变量 | snake_case | asset_list |

### 1.3 类型注解

所有公开函数必须有类型注解：

```python
async def get_asset(asset_id: str, db: AsyncSession) -> Asset | None:
    ...
```

### 1.4 文档字符串

```python
async def create_asset(data: AssetCreate, db: AsyncSession) -> Asset:
    """创建资产.

    Args:
        data: 资产创建数据
        db: 数据库会话

    Returns:
        创建的资产对象

    Raises:
        DuplicateError: 资产已存在
    """
```

### 1.5 异步优先

所有 I/O 操作使用 async/await。

### 1.6 依赖注入

使用 FastAPI Depends，不直接实例化 Service。

---

## 2. TypeScript 前端

### 2.1 工具

- **Lint：** ESLint
- **格式化：** Prettier

### 2.2 命名

| 类型 | 风格 | 示例 |
|---|---|---|
| 组件 | PascalCase | AssetList.vue |
| Composable | camelCase (use前缀) | useAssetList |
| 变量/函数 | camelCase | assetList |
| 常量 | UPPER_SNAKE | API_BASE_URL |
| 类型/接口 | PascalCase | AssetItem |

### 2.3 组件结构

```vue
<script setup lang="ts">
// 1. imports
// 2. composables
// 3. reactive state
// 4. computed
// 5. methods
// 6. lifecycle hooks
</script>

<template>
<!-- HTML -->
</template>

<style scoped>
/* CSS */
</style>
```
