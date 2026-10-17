<template>
  <page-layout>
    <a-card>
      <div class="guide-hero">
        <h2>{{ heading }}</h2>
        <p>{{ topic === 'register' ? '说明来自已入库的医院资料，不直接完成挂号。' : '只说明资料里写到的楼层和科室，没有坐标时不编造路线。' }}</p>
      </div>
      <div class="guide-steps">
        <div>
          <strong>1</strong>
          <span>{{ topic === 'register' ? '先看挂号、取号和就诊卡' : '先确认科室名称' }}</span>
        </div>
        <div>
          <strong>2</strong>
          <span>{{ topic === 'register' ? '再按资料里的窗口办理' : '对照资料中的楼层' }}</span>
        </div>
        <div>
          <strong>3</strong>
          <span>{{ topic === 'register' ? '线上问答不能代替现场取号' : '有楼层说明时才打开地图' }}</span>
        </div>
      </div>
      <a-input-search
        v-model="keyword"
        placeholder="例如：心内科在几楼，或怎么挂号"
        enter-button="查询"
        @search="load"
      />
      <p class="guide-text">{{ text }}</p>
      <a v-if="mapUrl" class="guide-map" :href="mapUrl" target="_blank" rel="noopener noreferrer">在地图中打开这段位置</a>
    </a-card>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { guide } from "@/services/userSettings";

export default {
  name: "VisitGuide",
  components: { PageLayout },
  data() {
    return {
      keyword: "",
      text: "正在查询资料…",
      place: "",
    };
  },
  computed: {
    topic() {
      return this.$route.query.topic === "register" ? "register" : "place";
    },
    heading() {
      return this.topic === "register" ? "挂号流程" : "位置导航";
    },
    mapUrl() {
      if (!this.place) return "";
      return "https://uri.amap.com/search?keyword=" + encodeURIComponent(this.place);
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
    load() {
      this.text = "正在查询资料…";
      this.place = "";
      guide({ topic: this.topic, query: this.keyword }).then(({ data }) => {
        if (data.code === 20000 && data.data) {
          this.text = data.data.text || "资料里没有对应说明。";
          this.place = data.data.place || "";
        } else {
          this.text = (data && data.data) || "暂时无法查询。";
        }
      }).catch(() => {
        this.text = "暂时无法查询，请稍后再试。";
      });
    },
  },
};
</script>

<style scoped>
.guide-hero h2 {
  margin: 0 0 6px;
}
.guide-hero p,
.guide-text {
  margin-top: 16px;
  white-space: pre-wrap;
  line-height: 1.7;
}
.guide-hero p {
  margin-top: 0;
  color: #595959;
}
.guide-steps {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin: 16px 0;
}
.guide-steps div {
  padding: 12px;
  background: #f7fbf8;
  border-radius: 8px;
}
.guide-steps strong {
  display: inline-block;
  width: 22px;
  height: 22px;
  margin-right: 8px;
  border-radius: 50%;
  background: #1e4636;
  color: #fff;
  text-align: center;
  line-height: 22px;
}

.guide-map {
  display: inline-block;
  margin-top: 8px;
}
</style>
