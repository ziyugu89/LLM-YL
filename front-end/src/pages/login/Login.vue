<template>
  <common-layout>
    <div class="top">
      <div class="header1">
        <span class="title1">“慧诊医伴”AI陪诊服务平台</span>
      </div>
      <div class="header2">
        <span class="title2">请登录</span>
      </div>
      <div class="desc">欢迎使用本系统</div>
    </div>
    <div class="login">
      <a-form @submit="onSubmit" :form="form">
        <a-alert
          type="error"
          :closable="true"
          v-show="error"
          :message="error"
          showIcon
          style="margin-bottom: 24px;"
        />
        <a-form-item>
          <a-input
            autocomplete="autocomplete"
            size="large"
            placeholder="账号"
            v-decorator="[
              'name',
              {
                rules: [
                  { required: true, message: '请输入账户名', whitespace: true },
                ],
              },
            ]"
          >
            <a-icon slot="prefix" type="user" />
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-input
            size="large"
            placeholder="密码"
            autocomplete="autocomplete"
            type="password"
            v-decorator="[
              'password',
              {
                rules: [
                  { required: true, message: '请输入密码', whitespace: true },
                ],
              },
            ]"
          >
            <a-icon slot="prefix" type="lock" />
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-button
            :loading="logging"
            style="width: 100%;margin-top: 24px"
            size="large"
            htmlType="submit"
            type="primary"
            >登录</a-button
          >
          <a-button
            :loading="logging"
            style="width: 100%;margin-top: 24px"
            size="large"
            @click="visible = true"
            >病患注册</a-button
          >
        </a-form-item>
      </a-form>

      <a-modal v-model="visible" title="病患注册" on-ok="handleOk">
        <template slot="footer">
          <a-button key="back" @click="closeModal">
            取消
          </a-button>
          <a-button
            key="submit"
            type="primary"
            :loading="loading"
            @click="handleOk"
          >
            注册
          </a-button>
        </template>
        <a-form :form="form2">
          <a-alert
            type="error"
            :closable="true"
            v-show="error"
            :message="error"
            showIcon
            style="margin-bottom: 24px;"
          />
          <a-form-item>
            <a-input
              autocomplete="autocomplete"
              size="large"
              placeholder="账号"
              v-decorator="[
                'user',
                {
                  rules: [
                    {
                      required: true,
                      message: '请输入账户名',
                      whitespace: true,
                    },
                  ],
                },
              ]"
            >
              <a-icon slot="prefix" type="user" />
            </a-input>
          </a-form-item>
          <a-form-item>
            <a-input
              size="large"
              placeholder="密码"
              autocomplete="autocomplete"
              type="password"
              v-decorator="[
                'pwd',
                {
                  rules: [
                    { required: true, message: '请输入密码', whitespace: true },
                  ],
                },
              ]"
            >
              <a-icon slot="prefix" type="lock" />
            </a-input>
          </a-form-item>
        </a-form>
      </a-modal>
    </div>
  </common-layout>
</template>

<script>
import CommonLayout from "@/layouts/CommonLayout";
import {
  login,
  // getRoutesConfig,
  getInfo,
} from "@/services/user";
import { addUser } from "@/services/userSettings";
import { setAuthorization } from "@/utils/request";
// import {loadRoutes} from '@/utils/routerUtil'
import { mapMutations } from "vuex";

export default {
  name: "Login",
  components: { CommonLayout },
  data() {
    return {
      logging: false,
      error: "",
      form: this.$form.createForm(this),
      form2: this.$form.createForm(this),
      visible: false,
      loading: false,
    };
  },
  computed: {
    systemName() {
      return this.$store.state.setting.systemName;
    },
  },
  methods: {
    ...mapMutations("account", ["setUser", "setID", "setPermissions", "setRoles"]),
    onSubmit(e) {
      e.preventDefault();
      this.form.validateFields((err) => {
        if (!err) {
          this.logging = true;
          const name = this.form.getFieldValue("name");
          const password = this.form.getFieldValue("password");
          login(name, password)
            .then(this.afterLogin)
            .catch(() => {
              this.logging = false;
            });
        }
      });
    },
    handleOk() {
      this.form2.validateFields((err) => {
        if (!err) {
          this.loading = true;
          const user = this.form2.getFieldValue("user");
          const pwd = this.form2.getFieldValue("pwd");
          addUser({ user, pwd, roles: ["2"] })
            .then(() => {
              this.$message.success("注册成功");
              this.closeModal();
            })
            .finally(() => {
              this.loading = false;
            });
        }
      });
    },
    closeModal() {
      this.visible = false;
      this.form2.resetFields();
    },
    afterLogin(res) {
      this.logging = false;
      getInfo(res.data.data.token).then((req) => {
        var { data } = req;
        const loginRes = data;
        if (loginRes.code >= 0) {
          const {
            name,
            // permissions,
            roles,
            id,
          } = loginRes.data;
          this.setUser(name);
          this.setID(id);
          // this.setPermissions(permissions)
          this.setRoles(roles);
          setAuthorization({
            token: loginRes.data.token,
            expireAt: new Date(loginRes.data.expireAt),
          });

          this.$router.push("/dashboard");
          this.$message.success(loginRes.message, 3);
          // 获取路由配置
          // getRoutesConfig().then(result => {
          //   const routesConfig = result.data.data
          //   loadRoutes(routesConfig)
          //   this.$router.push('/dashboard/workplace')
          //   this.$message.success(loginRes.message, 3)
          // })
        } else {
          this.error = loginRes.message;
        }
      });
    },
  },
};
</script>

<style lang="less" scoped>
.common-layout {
  .top {
    text-align: center;
    .header1 {
      .title1 {
        font-size: 60px;
        color:  rgba(58, 101, 229, 0.74);
        text-shadow: 3px 3px 6px rgba(0, 0, 0, 0.5);
        letter-spacing: 5px;
        font-family: "Myriad Pro", "Helvetica Neue", Arial, Helvetica,
        sans-serif;
        font-weight: 600;
        position: relative;
        top: 2px;
        
      }
      bottom: 40px;
      position: relative;
    }
    .header2{
      height: 44px;
      line-height: 44px;
      a {
        text-decoration: none;
      }
      .logo {
        height: 44px;
        vertical-align: top;
        margin-right: 16px;
      }

      .title2 {
        font-size: 33px;
        color: @title-color;
        font-family: "Myriad Pro", "Helvetica Neue", Arial, Helvetica,
          sans-serif;
        font-weight: 600;
        position: relative;
        top: 2px;
      }
    }
    .desc {
      font-size: 14px;
      color: @text-color-second;
      margin-top: 12px;
      margin-bottom: 40px;
    }
  }
  .login {
    width: 368px;
    margin: 0 auto;
    @media screen and (max-width: 576px) {
      width: 95%;
    }
    @media screen and (max-width: 320px) {
      .captcha-button {
        font-size: 14px;
      }
    }
    .icon {
      font-size: 24px;
      color: @text-color-second;
      margin-left: 16px;
      vertical-align: middle;
      cursor: pointer;
      transition: color 0.3s;

      &:hover {
        color: @primary-color;
      }
    }
  }
}
</style>
