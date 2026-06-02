# 独立监控体系设计（V1）

## 1. 目标

监控体系必须保持独立性，不能默认依赖被监控 Kubernetes 集群自身。

核心目标：

```text
业务集群故障时，监控仍然可用
控制面故障时，监控仍然可用
存储故障时，监控仍然可用
KubeVirt/CSI 异常时，监控仍然可用
```

因此本项目的监控设计采用：

```text
外部独立监控集群优先
业务集群内 agent/exporter 最小化部署
监控数据外置持久化
告警通道独立
```

---

## 2. 设计原则

必须遵循：

```text
1. 监控平面与业务平面解耦
2. 监控存储不依赖被监控集群 CSI
3. 告警通道不依赖被监控集群网络入口
4. 监控集群可以一套监控多套业务集群
5. 被监控集群内只部署最小采集组件
6. 监控系统故障不能影响业务集群
```

不建议：

```text
把 Prometheus/Grafana/Alertmanager 全部安装在生产业务集群内部
把监控数据放在被监控集群的默认 StorageClass 上
让业务集群 Ingress 故障导致监控不可访问
```

---

## 3. 推荐总体架构

```text
┌──────────────────────────────┐
│ External Observability Cluster│
│                              │
│ Prometheus / Thanos / Mimir   │
│ Alertmanager                  │
│ Grafana                       │
│ Loki / Tempo optional         │
└───────────────┬──────────────┘
                │ scrape / remote_write / alert
                │
┌───────────────▼──────────────┐
│ Business Kubernetes Cluster A │
│ node-exporter                 │
│ kube-state-metrics            │
│ kubelet/cAdvisor              │
│ kube-apiserver metrics        │
│ KubeVirt / CDI / CSI metrics  │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Business Kubernetes Cluster B │
│ same lightweight collectors   │
└──────────────────────────────┘
```

---

## 4. 三种部署模式

### 4.1 external 模式，推荐

监控组件部署在独立集群或独立 VM 上。

适合：

```text
生产环境
多集群管理
KubeVirt / CSI / Ceph 生产场景
```

优点：

```text
业务集群故障不影响监控
可以统一监控多集群
历史数据更安全
告警链路更稳定
```

---

### 4.2 hybrid 模式

监控核心在外部，agent/exporter 在业务集群内部。

适合：

```text
大多数企业环境
```

组件划分：

```text
外部：Prometheus / Thanos / Grafana / Alertmanager
内部：node-exporter / kube-state-metrics / service monitors / exporters
```

---

### 4.3 in-cluster 模式，仅测试

所有监控组件部署在被监控集群内部。

适合：

```text
PoC
开发测试
单节点验证
```

不建议生产使用。

---

## 5. 网络模型

推荐两种方式：

### 5.1 Pull 模式

外部 Prometheus 直接 scrape 业务集群指标。

要求：

```text
监控集群可以访问业务集群 kube-apiserver
监控集群可以访问 node-exporter/kubelet metrics
需要 TLS / RBAC / 网络 ACL
```

优点：

```text
集中控制
容易审计
```

缺点：

```text
跨网络访问复杂
防火墙规则较多
```

---

### 5.2 Push / remote_write 模式

业务集群内轻量 Prometheus Agent 采集后 remote_write 到外部系统。

适合：

```text
网络隔离环境
边缘集群
多租户环境
```

优点：

```text
减少外部入站访问
更适合跨网络
```

缺点：

```text
业务集群内仍需运行轻量 agent
agent 故障会影响当前集群指标上报
```

---

## 6. 监控数据存储

生产建议：

```text
独立对象存储
独立块存储
外部 Ceph / S3 / MinIO / 企业存储
```

不建议：

```text
把 Prometheus TSDB 放在被监控集群的业务 StorageClass 上
把长期历史数据放在单节点 local-lvm 上
```

推荐：

```text
短期数据：Prometheus 本地盘
长期数据：Thanos / Mimir / VictoriaMetrics / 对象存储
```

---

## 7. 监控对象

必须覆盖：

```text
Kubernetes control-plane
etcd
node
container runtime
CNI
CSI
StorageClass / PVC / PV
KubeVirt
CDI
VM / VMI
Ceph / iSCSI / NFS
HA LB / VIP
证书有效期
备份任务
```

---

## 8. KubeVirt 监控

重点指标：

```text
VM Running / Stopped / Error
VMI phase
virt-handler health
virt-api health
virt-controller health
VM CPU / Memory / Disk / Network
migration status
```

告警：

```text
VMI not ready
VM scheduling failed
virt-handler down
VM high memory pressure
VM disk IO error
```

---

## 9. CSI / 存储监控

重点指标：

```text
PVC pending
PV released/failed
VolumeAttachment failed
CSI controller error
CSI node plugin down
StorageClass capacity
Ceph health
Ceph OSD down
iSCSI session lost
NFS mount error
```

---

## 10. 告警独立性

Alertmanager 建议部署在外部监控集群。

告警通道应独立于业务集群：

```text
Email
Webhook
企业微信/钉钉/飞书
PagerDuty
短信网关
```

不建议：

```text
告警 webhook 服务跑在被监控集群内部
```

---

## 11. Inventory 设计建议

新增：

```yaml
observability_mode: external
# external | hybrid | in_cluster

observability_enabled: false
observability_cluster_name: ops-monitoring

observability_prometheus_endpoint: ""
observability_remote_write_endpoint: ""
observability_alertmanager_endpoint: ""
observability_grafana_endpoint: ""

observability_install_in_cluster_stack: false
observability_install_agent: true
observability_scrape_mode: pull
# pull | remote_write
```

---

## 12. Playbook 设计建议

建议拆分：

```text
0080-observability-preflight.yml
0081-observability-agent.yml
0082-observability-external-targets.yml
0083-observability-rules.yml
0084-observability-dashboards.yml
0085-observability-slo-report.yml
```

其中：

```text
0081 只在业务集群安装轻量 agent/exporter
0082 在外部监控系统注册 scrape target
0083 管理告警规则
0084 管理 Grafana dashboards
0085 生成 SLO/容量/健康报告
```

---

## 13. 推荐落地顺序

```text
1. 文档设计
2. observability inventory
3. preflight 检查外部监控端点
4. 业务集群轻量 agent/exporter
5. 外部 Prometheus targets
6. 告警规则
7. Grafana dashboards
8. SLO 报告
```

---

## 14. 最终结论

监控必须作为独立平面：

```text
业务集群负责运行 workload
存储平面负责数据
虚拟化平面负责 VM
治理层负责检查
监控平面负责持续观测和告警
```

其中监控平面应优先部署在：

```text
独立 Kubernetes 集群
独立 VM 集群
独立运维区
```

而不是默认部署在被监控集群内部。
