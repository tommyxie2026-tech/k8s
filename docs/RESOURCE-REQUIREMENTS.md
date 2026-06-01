# 项目最小运行资源评估（V1）

## 1. 目标

本文档用于评估本项目在不同运行场景下的最小资源需求。

覆盖能力包括：

```text
Kubernetes 基础集群
single-node
HA control-plane
CSI 存储
KubeVirt 虚拟化
CDI / DataVolume
生产级 HA
```

本文档中的资源规格分为：

```text
最低可运行
推荐可用
生产建议
不建议边界
```

说明：

```text
最低可运行 ≠ 生产可用
最低可运行只表示组件能够启动并完成基础验证
```

---

## 2. 资源维度

评估维度：

```text
CPU
内存
系统盘
数据盘
网络
节点数量
硬件虚拟化能力
```

特殊要求：

```text
KubeVirt 需要 /dev/kvm
CSI 需要可用 StorageClass
Rook Ceph 需要独立数据盘
iSCSI SAN 需要存储网络与 multipath
```

---

## 3. 场景一：仅运行 ansible / syntax-check / 文档开发

适合：

```text
代码开发
CI 语法检查
文档维护
不真正部署 Kubernetes
```

最低资源：

| 资源 | 最低 |
|---|---:|
| CPU | 2 核 |
| 内存 | 4 GiB |
| 磁盘 | 20 GiB |
| 节点数 | 1 |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| CPU | 4 核 |
| 内存 | 8 GiB |
| 磁盘 | 40 GiB |

说明：

```text
该场景不需要 /dev/kvm
不需要额外数据盘
不需要真实 Kubernetes 集群
```

---

## 4. 场景二：单节点 Kubernetes 基础集群

适合：

```text
PoC
开发测试
最小 Kubernetes 验证
单节点边缘环境
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 1 |
| CPU | 4 核 |
| 内存 | 8 GiB |
| 系统盘 | 80 GiB |
| 网络 | 1GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| CPU | 8 核 |
| 内存 | 16 GiB |
| 系统盘 | 100-200 GiB |
| 网络 | 1/10GbE |

可运行能力：

```text
kube-apiserver
kube-controller-manager
kube-scheduler
etcd
kubelet
CNI
基础 Pod
```

不建议：

```text
在该规格上运行生产业务
在系统盘上混跑大量数据型 workload
```

---

## 5. 场景三：单节点 + local-lvm CSI

适合：

```text
单节点 StatefulSet 测试
边缘节点
轻量 VM 测试
本地盘高性能场景
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 1 |
| CPU | 4 核 |
| 内存 | 12 GiB |
| 系统盘 | 80 GiB |
| 数据盘 | 100 GiB |
| 网络 | 1GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| CPU | 8 核 |
| 内存 | 16-32 GiB |
| 系统盘 | 100 GiB |
| 数据盘 | 200 GiB+ SSD/NVMe |

说明：

```text
local-lvm 适合单节点或边缘场景
不支持跨节点漂移
节点故障会带来数据风险
```

不建议：

```text
把核心生产数据库只放在 local-lvm 上
把 local-lvm 作为 HA 默认存储
```

---

## 6. 场景四：三节点 HA control-plane

适合：

```text
控制面高可用
single → HA 演进
小型生产基础集群
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 3 |
| 每节点 CPU | 4 核 |
| 每节点内存 | 8 GiB |
| 每节点系统盘 | 100 GiB |
| 网络 | 1GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| 节点数 | 3 |
| 每节点 CPU | 8 核 |
| 每节点内存 | 16 GiB |
| 每节点系统盘 | 100-200 GiB SSD |
| 网络 | 10GbE |

可运行能力：

```text
HA etcd
HA kube-apiserver
VIP / keepalived / nginx
CNI
基础 workload
```

说明：

```text
该规格只解决控制面 HA
不等于存储 HA
```

---

## 7. 场景五：HA + NFS CSI

适合：

```text
小型共享目录
低成本共享存储
配置文件/日志/低 IO workload
```

最低资源：

| 资源 | 最低 |
|---|---:|
| Kubernetes 节点 | 3 |
| NFS 节点 | 1 |
| K8s 每节点 CPU | 4 核 |
| K8s 每节点内存 | 8-16 GiB |
| NFS 数据盘 | 200 GiB+ |
| 网络 | 1GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| Kubernetes 节点 | 3+ |
| NFS 节点 | 1-2 |
| K8s 每节点 CPU | 8 核 |
| K8s 每节点内存 | 16 GiB+ |
| NFS 数据盘 | SSD / RAID |
| 网络 | 10GbE |

不建议：

```text
高 IO 数据库
高并发 VM 数据盘
强一致事务型生产 workload
```

---

## 8. 场景六：HA + iSCSI SAN

适合：

```text
已有企业 SAN
数据库
企业级块存储
高性能 StatefulSet
KubeVirt VM 数据盘
```

最低资源：

| 资源 | 最低 |
|---|---:|
| Kubernetes 节点 | 3 |
| 每节点 CPU | 4-8 核 |
| 每节点内存 | 16 GiB |
| SAN | 已有可用 iSCSI target |
| 网络 | 10GbE 推荐，最低 1GbE |
| multipath | 必须 |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| Kubernetes 节点 | 3+ |
| 每节点 CPU | 8-16 核 |
| 每节点内存 | 32 GiB+ |
| 存储网络 | 独立 VLAN / 10GbE+ |
| iSCSI portal | 双 portal+ |
| multipath | 必须启用 |
| CHAP | 必须启用 |

说明：

```text
iSCSI 更像企业块设备接入协议
生产建议优先使用厂商 CSI
```

不建议：

```text
单 portal
无 CHAP
无 multipath
直接 static PV 大规模生产
```

---

## 9. 场景七：HA + Rook Ceph

适合：

```text
云原生企业存储
多副本块存储
CephFS 共享文件
KubeVirt VM 数据盘
企业 StatefulSet
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 3 |
| 每节点 CPU | 8 核 |
| 每节点内存 | 32 GiB |
| 每节点系统盘 | 100 GiB SSD |
| 每节点数据盘 | 1 块独立数据盘 |
| 网络 | 10GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| 节点数 | 3-5+ |
| 每节点 CPU | 16 核+ |
| 每节点内存 | 64 GiB+ |
| 每节点数据盘 | 2 块以上 SSD/NVMe |
| 网络 | 10/25GbE |
| Ceph replica | 3 |

说明：

```text
Ceph 不建议与极低资源节点混跑
OSD 不建议使用系统盘
生产应使用独立数据盘
```

不建议：

```text
3 台以下做生产 Ceph
系统盘混做 OSD
1GbE 网络承载高 IO Ceph
```

---

## 10. 场景八：单节点 KubeVirt

适合：

```text
KubeVirt 功能验证
轻量 VM 测试
边缘虚拟机管理
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 1 |
| CPU | 8 核 |
| 内存 | 16 GiB |
| 系统盘 | 100 GiB |
| 数据盘 | 100 GiB+ |
| /dev/kvm | 必须，除非启用 emulation |
| 网络 | 1GbE |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| CPU | 12-16 核 |
| 内存 | 32-64 GiB |
| 数据盘 | SSD/NVMe 200 GiB+ |
| 网络 | 10GbE |

说明：

```text
单节点 KubeVirt 可以管理 VM
但无法提供 VM 高可用和跨节点迁移
```

不建议：

```text
生产级 VM
依赖单节点承载关键业务
无 /dev/kvm 时启用生产 VM
```

---

## 11. 场景九：HA + KubeVirt

适合：

```text
容器 + 虚拟机混合平台
传统应用迁移
轻量私有云
企业 VM 管理
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 3 |
| 每节点 CPU | 8 核 |
| 每节点内存 | 32 GiB |
| 每节点系统盘 | 100 GiB |
| 存储 | local-lvm / NFS / iSCSI / Ceph |
| /dev/kvm | 必须 |
| 网络 | 10GbE 推荐 |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| 节点数 | 3-5+ |
| 每节点 CPU | 16-32 核 |
| 每节点内存 | 64-128 GiB |
| VM 存储 | Rook Ceph RBD / iSCSI SAN |
| 网络 | 10/25GbE |

说明：

```text
KubeVirt 本身只提供虚拟化编排能力
VM 的稳定性强依赖底层 CSI / CNI / KVM / 节点资源
```

不建议：

```text
用 NFS 承载高 IO VM 数据盘
无硬件虚拟化时运行生产 VM
存储未 HA 时承载关键 VM
```

---

## 12. 场景十：HA + KubeVirt + CDI / DataVolume

适合：

```text
镜像导入
PVC-backed VM
传统 VM 镜像迁移
DataVolume 测试
```

最低资源：

| 资源 | 最低 |
|---|---:|
| 节点数 | 3 |
| 每节点 CPU | 8-16 核 |
| 每节点内存 | 32 GiB |
| 存储 | 可动态 provision 的 StorageClass |
| 镜像缓存空间 | 100 GiB+ |
| 网络 | 10GbE 推荐 |

推荐资源：

| 资源 | 推荐 |
|---|---:|
| 每节点 CPU | 16-32 核 |
| 每节点内存 | 64 GiB+ |
| 存储 | Ceph RBD / iSCSI SAN |
| 镜像缓存空间 | 500 GiB+ |
| 网络 | 10/25GbE |

说明：

```text
CDI 会产生 importer pod
镜像导入过程会消耗网络、磁盘 IO 和临时空间
```

不建议：

```text
在低速 NFS 上频繁导入大镜像
在无可用 StorageClass 时启用 DataVolume 测试
```

---

## 13. 场景十一：生产级企业 HA 平台

适合：

```text
企业 Kubernetes 交付平台
容器 + VM 混合负载
关键 StatefulSet
生产 VM
```

推荐生产下限：

| 资源 | 推荐下限 |
|---|---:|
| 节点数 | 5+ |
| control-plane | 3 台独立节点 |
| worker/storage | 3 台以上 |
| 每节点 CPU | 16-32 核 |
| 每节点内存 | 64-128 GiB |
| 系统盘 | 200 GiB SSD |
| 数据盘 | 多块 SSD/NVMe |
| 网络 | 10/25GbE |
| 存储 | Rook Ceph / 企业 SAN |
| 备份 | 必须 |
| 监控 | 必须 |

生产必须具备：

```text
etcd snapshot
证书检查
CSI health-check
PVC/PV 迁移策略
KubeVirt health-check
备份恢复
节点故障演练
```

不建议：

```text
3 台小规格节点承载控制面 + Ceph + VM + 业务
无备份运行生产 StatefulSet
无存储 HA 运行生产 VM
```

---

## 14. 最小资源决策表

| 场景 | 最小节点 | 最低 CPU/节点 | 最低内存/节点 | 存储要求 | 适合 |
|---|---:|---:|---:|---|---|
| syntax-check | 1 | 2 核 | 4 GiB | 20 GiB | CI/开发 |
| single k8s | 1 | 4 核 | 8 GiB | 80 GiB | PoC |
| single + local-lvm | 1 | 4 核 | 12 GiB | 独立数据盘 | 边缘/测试 |
| HA control-plane | 3 | 4 核 | 8 GiB | 系统盘 | 控制面 HA |
| HA + NFS | 3+1 | 4 核 | 8-16 GiB | NFS | 轻量共享 |
| HA + iSCSI | 3 | 4-8 核 | 16 GiB | 企业 SAN | 企业块存储 |
| HA + Ceph | 3 | 8 核 | 32 GiB | 独立数据盘 | 云原生存储 |
| single KubeVirt | 1 | 8 核 | 16 GiB | /dev/kvm + 数据盘 | VM 测试 |
| HA + KubeVirt | 3 | 8 核 | 32 GiB | CSI + /dev/kvm | 混合负载 |
| HA + KubeVirt + CDI | 3 | 8-16 核 | 32 GiB | 动态 StorageClass | 镜像导入 |
| 生产企业平台 | 5+ | 16-32 核 | 64-128 GiB | Ceph/SAN | 生产 |

---

## 15. 推荐部署路径

最低验证路径：

```text
single Kubernetes
→ local-lvm
→ KubeVirt ephemeral VM smoke test
```

小型 HA 路径：

```text
HA control-plane
→ NFS/local-lvm
→ KubeVirt
```

企业路径：

```text
HA control-plane
→ iSCSI SAN 或 Rook Ceph
→ KubeVirt
→ CDI
→ DataVolume smoke test
```

生产路径：

```text
HA control-plane
→ 企业 CSI
→ 备份恢复
→ KubeVirt
→ CDI
→ VM 生命周期运维
→ 故障演练
```

---

## 16. 硬性不建议边界

不建议：

```text
1. 低于 4C/8G 跑完整 Kubernetes
2. 低于 8C/16G 跑 KubeVirt
3. 低于 3 节点跑生产 HA
4. 无独立数据盘跑生产 Ceph
5. 无 /dev/kvm 跑生产 VM
6. 无备份跑生产 StatefulSet
7. 无 CSI health-check 跑生产 VM
8. 用 latest / beta / rc 版本部署生产 KubeVirt
```

---

## 17. 结论

本项目最小运行资源可以分三档：

```text
开发验证档：2C/4G 起
单节点功能档：4C/8G 起
KubeVirt 虚拟化档：8C/16G 起
企业生产档：5 节点、16C/64G 起
```

最终建议：

```text
不要用最低配置定义生产能力
最低配置只用于验证组件是否能跑通
生产能力必须按 HA、存储、备份、网络和故障演练综合评估
```
