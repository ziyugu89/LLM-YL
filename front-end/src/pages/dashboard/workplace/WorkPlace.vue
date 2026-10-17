<template>
  <page-layout :avatar="userLogo">
    <div slot="headerContent" class="home-head">
      <div class="title">{{ greeting }}，{{ profile.name || currUser }}</div>
      <div class="home-meta">
        <span class="role-pill">{{ profile.roleText || "已登录" }}</span>
        <span v-if="profile.pcode">就诊编号 {{ profile.pcode }}</span>
        <span v-else>下面只显示当前身份可以使用的功能</span>
      </div>
    </div>
    <a-card v-for="group in groups" :key="group.title" class="svc-card" :title="group.title">
      <div class="svc-grid">
        <button
          v-for="item in group.items"
          :key="item.title"
          type="button"
          class="svc-btn"
          @click="open(item)"
        >
          <span class="svc-icon" :style="{ background: group.tint, color: group.ink }">
            <a-icon :type="item.icon" />
          </span>
          <span class="svc-label">{{ item.title }}</span>
        </button>
      </div>
    </a-card>
    <a-card class="home-note" title="使用说明">
      <ul>
        <li v-for="line in notes" :key="line">{{ line }}</li>
      </ul>
    </a-card>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { mapState } from "vuex";
import userLogo from "@/assets/img/user.jpg";
import { profile } from "@/services/user";

const SERVICES = [
  {
    title: "门诊服务",
    tint: "#e7f2ec",
    ink: "#1e4636",
    items: [
      { title: "智能导诊", path: "/llm", icon: "message", roles: ["patient", "admin"] },
      { title: "预约挂号", path: "/guide", query: { topic: "register" }, icon: "calendar", roles: ["patient", "doctor", "admin"] },
      { title: "号源查询", path: "/hospital", query: { topic: "slots" }, icon: "schedule", roles: ["patient", "doctor", "admin"] },
      { title: "候诊排队", path: "/hospital", query: { topic: "queue" }, icon: "clock-circle", roles: ["patient", "doctor", "admin"] },
      { title: "院内导航", path: "/guide", query: { topic: "place" }, icon: "environment", roles: ["patient", "doctor", "admin"] },
    ],
  },
  {
    title: "健康档案",
    tint: "#f8efe6",
    ink: "#8a4b2f",
    items: [
      { title: "我的病历", path: "/imgbh", icon: "file-text", roles: ["patient", "admin"] },
      { title: "检查报告", path: "/hospital", query: { topic: "reports" }, icon: "file-search", roles: ["patient", "doctor", "admin"] },
      { title: "建立病历", path: "/img", icon: "form", roles: ["doctor", "admin"] },
      { title: "用药提醒", path: "/img", query: { panel: "remind" }, icon: "bell", roles: ["doctor", "admin"] },
    ],
  },
  {
    title: "就医管理",
    tint: "#eef1f4",
    ink: "#243046",
    items: [
      { title: "患者查询", path: "/patients", icon: "search", roles: ["doctor", "admin"] },
      { title: "账号管理", path: "/userSettings", icon: "team", roles: ["admin"] },
    ],
  },
];

const NOTES = {
  patient: [
    "挂号和导航根据医院资料说明流程，不会直接完成挂号。",
    "号源、排队和检查报告只有导入资料后才能看到，看不到时不会编造。",
    "病历只显示本人记录。右上角可以修改密码或注销本次登录。",
  ],
  doctor: [
    "可以用 8 位就诊编号建立病历，并设置用药提醒。",
    "可以查询患者，也可以查看已导入的号源、排队和检查报告。",
    "不能进入问诊页，也不能注销账号。",
  ],
  admin: [
    "可以进入全部功能，并管理患者、医生和管理员账号。",
    "新建患者时会分配 8 位就诊编号。",
    "注销后的账号不能再登录。初始管理员账号不能被注销。",
  ],
};

export default {
  name: "WorkPlace",
  components: { PageLayout },
  data() {
    return {
      userLogo,
      profile: { name: "", roleText: "", pcode: "", roles: [] },
    };
  },
  computed: {
    ...mapState("account", { currUser: "user" }),
    kind() {
      const roles = this.profile.roles || [];
      if (roles.indexOf("admin") >= 0) return "admin";
      if (roles.indexOf("doctor") >= 0) return "doctor";
      return "patient";
    },
    groups() {
      return SERVICES.map((group) => ({
        ...group,
        items: group.items.filter((item) => item.roles.indexOf(this.kind) >= 0),
      })).filter((group) => group.items.length);
    },
    notes() {
      return NOTES[this.kind];
    },
    greeting() {
      const hour = new Date().getHours();
      if (hour < 11) return "早上好";
      if (hour < 18) return "下午好";
      return "晚上好";
    },
  },
  created() {
    profile().then(({ data }) => {
      if (data.code === 20000 && data.data) this.profile = data.data;
    }).catch(() => {});
  },
  methods: {
    open(item) {
      this.$router.push({ path: item.path, query: item.query || {} });
    },
  },
};
</script>

<style lang="less" scoped>
.home-head .title {
  font-size: 20px;
  font-weight: 600;
}
.home-meta {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 8px;
}
.role-pill {
  padding: 2px 10px;
  border-radius: 12px;
  background: #e6f4ef;
  color: #1e4636;
}
.svc-card {
  margin-bottom: 16px;
}
.svc-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px 4px;
}
.svc-btn {
  border: 0;
  background: transparent;
  padding: 8px 4px 4px;
  cursor: pointer;
}
.svc-icon {
  width: 52px;
  height: 52px;
  margin: 0 auto 8px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
}
.svc-label {
  display: block;
  color: #1c1915;
  font-size: 14px;
  line-height: 1.4;
}
.home-note li {
  line-height: 1.9;
}
@media screen and (max-width: 720px) {
  .svc-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
