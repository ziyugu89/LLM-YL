<template>
  <common-layout>
    <div class="top">
      <div class="header1">
        <span class="title1">“慧诊医伴”AI陪诊服务平台</span>
      </div>
      <div class="header2">
        <span class="title2">{{ heading }}</span>
      </div>
      <div class="desc">请先选择身份，再输入账号和密码</div>
    </div>
    <div class="login">
      <div class="login-panel">
      <div class="role-pick">
        <button type="button" :class="{ active: role === 'use' }" @click="choose('use')">
          <strong>患者</strong>
          <span>问诊与本人病历</span>
        </button>
        <button type="button" :class="{ active: role === 'doctor' }" @click="choose('doctor')">
          <strong>医生</strong>
          <span>建病历与查患者</span>
        </button>
        <button type="button" :class="{ active: role === 'admin' }" @click="choose('admin')">
          <strong>管理员</strong>
          <span>账号增删与注销</span>
        </button>
      </div>
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
            >{{ loginText }}</a-button
          >
          <a-button
            v-if="role === 'use'"
            :loading="logging"
            style="width: 100%;margin-top: 12px"
            size="large"
            @click="visible = true"
            >病患注册</a-button
          >
        </a-form-item>
      </a-form>
      </div>

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
      role: "",
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
    roleTitle() {
      return { use: "患者登录", doctor: "医生登录", admin: "管理员登录" }[this.role] || "";
    },
    heading() {
      return this.roleTitle || "请选择身份";
    },
    loginText() {
      return this.roleTitle || "登录";
    },
  },
  methods: {
    ...mapMutations("account", ["setUser", "setID", "setPermissions", "setRoles"]),
    choose(role) {
      this.role = role;
      this.error = "";
    },
    onSubmit(e) {
      e.preventDefault();
      if (!this.role) {
        this.error = "请先选择患者、医生或管理员";
        return;
      }
      this.form.validateFields((err) => {
        if (!err) {
          this.logging = true;
          const name = this.form.getFieldValue("name");
          const password = this.form.getFieldValue("password");
          login(name, password, this.role)
            .then((res) => {
              if (!res.data || res.data.code !== 20000) {
                this.logging = false;
                this.error = (res.data && res.data.data) || "登录失败";
                return;
              }
              this.afterLogin(res);
            })
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
            .then(({ data }) => {
              const pcode = data && data.data && data.data.pcode;
              if (data && data.code === 20000) {
                this.$message.success(pcode ? `注册成功，就诊编号 ${pcode}` : "注册成功");
                this.closeModal();
              } else {
                this.$message.error((data && data.data) || "注册失败");
              }
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
        if (loginRes.code === 20000 && loginRes.data) {
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
        color: #1e4636;
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
    width: 480px;
    margin: 0 auto;
    @media screen and (max-width: 576px) {
      width: 95%;
    }
    @media screen and (max-width: 320px) {
      .captcha-button {
        font-size: 14px;
      }
    }
    .login-panel {
      padding: 22px 22px 8px;
      background: rgba(255, 253, 248, 0.94);
      border: 1px solid #e4ddd0;
      border-top: 4px solid #1e4636;
      border-radius: 12px;
    }
    .role-pick {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 8px;
      margin-bottom: 18px;
      button {
        padding: 12px 8px;
        border: 1px solid #d9d9d9;
        border-radius: 8px;
        background: rgba(255, 255, 255, 0.86);
        cursor: pointer;
        line-height: 1.4;
      }
      button.active {
        border-color: #1e4636;
        background: #f3f7f4;
        color: #1e4636;
      }
      strong, span {
        display: block;
      }
      span {
        margin-top: 4px;
        color: @text-color-second;
        font-size: 12px;
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
