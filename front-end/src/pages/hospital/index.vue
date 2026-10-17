<template>
  <page-layout>
    <a-card>
      <div class="feed-hero">
        <div>
          <h2>医院实时资料</h2>
          <p>号源、排队和检查报告分开查看。没有导入文件时，这里不会编造记录。</p>
        </div>
        <p class="feed-status">{{ statusText }}</p>
      </div>
      <div class="feed-summary">
        <button type="button" :class="{ active: kind === 'slots' }" @click="switchKind('slots')">
          <strong>{{ counts.slots }}</strong>
          <span>可查看号源</span>
        </button>
        <button type="button" :class="{ active: kind === 'queue' }" @click="switchKind('queue')">
          <strong>{{ counts.queue }}</strong>
          <span>可查看排队</span>
        </button>
        <button type="button" :class="{ active: kind === 'reports' }" @click="switchKind('reports')">
          <strong>{{ counts.reports }}</strong>
          <span>可查看报告</span>
        </button>
      </div>
      <a-input-search
        v-model="keyword"
        placeholder="按科室、医生、号码或项目筛选"
        enter-button="查询"
        @search="load"
      />
      <p v-if="message" class="feed-message">{{ message }}</p>
      <table v-if="items.length" class="feed-table">
        <thead>
          <tr>
            <th v-for="column in columns" :key="column.key">{{ column.title }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id">
            <td v-for="column in columns" :key="column.key">{{ item[column.key] }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!ready" class="feed-help">
        <p>把医院导出的资料保存为 hospital_feed/feed.json，保存后刷新本页即可。</p>
        <p>号源 slots：department 科室，doctor 医生，date 日期，period 时段，remain 剩余数量，place 地点。</p>
        <p>排队 queues：patient_id 填 8 位就诊编号，patient_name 姓名，department 科室，room 诊室，number 号码，ahead 前面人数，status 状态。</p>
        <p>检查报告 reports：patient_id 填 8 位就诊编号，patient_name 姓名，item 项目，time 时间，summary 报告原文，status 状态。</p>
        <p>患者只能看到与自己就诊编号一致的排队和报告。医生和管理员可以查看已导入的全部记录。这里只展示原文，不据此下诊断。</p>
      </div>
    </a-card>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { hospital } from "@/services/userSettings";

const COLUMNS = {
  slots: [
    { key: "department", title: "科室" },
    { key: "doctor", title: "医生" },
    { key: "date", title: "日期" },
    { key: "period", title: "时段" },
    { key: "remain", title: "剩余" },
    { key: "place", title: "地点" },
  ],
  queue: [
    { key: "patient_name", title: "就诊人" },
    { key: "department", title: "科室" },
    { key: "room", title: "诊室" },
    { key: "number", title: "号码" },
    { key: "ahead", title: "前面人数" },
    { key: "status", title: "状态" },
  ],
  reports: [
    { key: "patient_name", title: "就诊人" },
    { key: "item", title: "项目" },
    { key: "time", title: "时间" },
    { key: "status", title: "状态" },
    { key: "summary", title: "原文" },
  ],
};

export default {
  name: "HospitalFeed",
  components: { PageLayout },
  data() {
    return {
      kinds: [
        { id: "slots", title: "号源" },
        { id: "queue", title: "排队" },
        { id: "reports", title: "检查报告" },
      ],
      keyword: "",
      ready: false,
      message: "",
      items: [],
      counts: { slots: 0, queue: 0, reports: 0 },
      skipped: 0,
    };
  },
  computed: {
    kind() {
      return ["slots", "queue", "reports"].indexOf(this.$route.query.topic) >= 0
        ? this.$route.query.topic
        : "slots";
    },
    columns() {
      return COLUMNS[this.kind];
    },
    statusText() {
      if (!this.ready) return "尚未导入，当前不能提供实时号源、排队或检查报告。";
      const skipped = this.skipped ? `，另有 ${this.skipped} 条因缺少必填项未使用` : "";
      return `已导入，当前可查看号源 ${this.counts.slots} 条、排队 ${this.counts.queue} 条、检查报告 ${this.counts.reports} 条${skipped}。`;
    },
  },
  watch: {
    "$route.query": {
      handler() {
        this.keyword = this.$route.query.q || "";
        this.load();
      },
    },
  },
  created() {
    this.keyword = this.$route.query.q || "";
    this.load();
  },
  methods: {
    switchKind(kind) {
      this.$router.push({ path: "/hospital", query: { topic: kind, q: this.keyword } });
    },
    load() {
      this.message = "正在读取导入资料…";
      hospital({ kind: this.kind, query: this.keyword }).then(({ data }) => {
        if (data.code === 20000 && data.data) {
          this.ready = !!data.data.ready;
          this.message = data.data.message || "";
          this.items = data.data.items || [];
          this.counts = data.data.counts || this.counts;
          this.skipped = data.data.skipped || 0;
        } else {
          this.ready = false;
          this.items = [];
          this.message = (data && data.data) || "暂时无法读取。";
        }
      }).catch(() => {
        this.ready = false;
        this.items = [];
        this.message = "暂时无法读取，请稍后再试。";
      });
    },
  },
};
</script>

<style scoped>
.feed-hero {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.feed-hero h2 {
  margin: 0 0 6px;
}
.feed-hero p,
.feed-status,
.feed-message,
.feed-help p {
  line-height: 1.7;
  margin-bottom: 0;
}
.feed-summary {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.feed-summary button {
  padding: 14px;
  text-align: left;
  border: 1px solid #e6efe9;
  border-radius: 8px;
  background: #f7fbf8;
  cursor: pointer;
}
.feed-summary button.active {
  border-color: #1e4636;
  background: #eef6f1;
}
.feed-summary strong {
  display: block;
  font-size: 24px;
  color: #1e4636;
}
.feed-summary span {
  color: #595959;
}

.feed-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.feed-tabs button {
  padding: 4px 12px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  background: #fff;
  cursor: pointer;
}

.feed-tabs button.active {
  color: #1890ff;
  border-color: #1890ff;
}

.feed-table {
  width: 100%;
  margin-top: 16px;
  border-collapse: collapse;
}

.feed-table th,
.feed-table td {
  padding: 8px 10px;
  border-bottom: 1px solid #f0f0f0;
  text-align: left;
  vertical-align: top;
}

.feed-help {
  margin-top: 16px;
  color: #595959;
}
</style>
