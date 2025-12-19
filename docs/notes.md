## MVP V0.5
1. POST /ingest：导入 PDF（先支持本地 path，后面再支持 upload）
2. POST /search：query + topk → 返回 chunks + score + page
3. POST /reindex：重建/更新索引（最开始可以同步执行）