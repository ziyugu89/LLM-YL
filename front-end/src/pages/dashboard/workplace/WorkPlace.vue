<style lang="less" scoped>
.extraImg {
  margin-top: -60px;
  text-align: center;
  width: 195px;
  img {
    width: 100%;
  }
}
</style>

<template>
  <page-layout :avatar="userLogo">
    <div slot="headerContent">
      <div class="title">
        {{ welcome.timeFix[lang] }}，{{ currUser }}{{$t('id')}}{{ userid }}
      </div>
      <div>{{$t('greet')}}</div>
    </div>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { mapState } from "vuex";
import { request, METHOD } from "@/utils/request";
import userLogo from "@/assets/img/user.jpg";

export default {
  name: "WorkPlace",
  components: {

    PageLayout,
  },
  i18n: require("./i18n"),
  data() {
    return {
      projects: [],
      loading: true,
      activities: [],
      teams: [],
      welcome: {
        timeFix: "",
        message: "",
      },
      userLogo,
    };
  },
  computed: {
    ...mapState("account", { currUser: "user", userid: 'id' }),
    ...mapState("setting", ["lang"]),
  },
  created() {
    request("/user/welcome", METHOD.GET).then(
      (res) => (this.welcome = res.data)
    );
    request("/work/activity", METHOD.GET).then(
      (res) => (this.activities = res.data)
    );
    request("/work/team", METHOD.GET).then((res) => (this.teams = res.data));
    request("/project", METHOD.GET).then((res) => {
      this.projects = res.data;
      this.loading = false;
    });
  },
};
</script>

<style lang="less">
@import "index";
</style>
