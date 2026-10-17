<template>
  <page-layout>
    <a-card title="患者查询">
      <p class="patient-lead">这里只列出患者。可按姓名、账号或 8 位就诊编号查询。医生不能在这里注销账号。</p>
      <a-input-search
        v-model="keyword"
        placeholder="姓名、账号或就诊编号"
        enter-button="查询"
        style="max-width: 360px"
        @search="load"
      />
      <a-table
        style="margin-top: 16px"
        :columns="columns"
        :data-source="rows"
        :pagination="false"
        row-key="id"
      />
      <p v-if="message" class="patient-lead">{{ message }}</p>
    </a-card>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { getList } from "@/services/userSettings";

export default {
  name: "Patients",
  components: { PageLayout },
  data() {
    return {
      keyword: "",
      rows: [],
      message: "",
      columns: [
        { title: "就诊编号", dataIndex: "pcode", customRender: (text) => text || "—" },
        { title: "姓名", dataIndex: "name" },
        { title: "账号", dataIndex: "user" },
        { title: "状态", dataIndex: "status", customRender: (text) => (text == 1 ? "正常" : "已注销") },
      ],
    };
  },
  created() {
    this.load();
  },
  methods: {
    load() {
      this.message = "";
      getList({ page: 1, keyword: this.keyword }).then(({ data }) => {
        if (data.code === 20000 && data.data) {
          this.rows = data.data.list || [];
          this.message = this.rows.length ? "" : "没有符合条件的患者。";
        } else {
          this.rows = [];
          this.message = (data && data.data) || "暂时无法查询。";
        }
      }).catch(() => {
        this.message = "暂时无法查询，请稍后再试。";
      });
    },
  },
};
</script>

<style scoped>
.patient-lead {
  line-height: 1.7;
  color: #595959;
}
</style>
