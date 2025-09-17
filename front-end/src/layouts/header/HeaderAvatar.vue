<template>
  <a-dropdown>
    <div class="header-avatar" style="cursor: pointer">
      <a-avatar class="avatar" size="small" shape="circle" :src="userLogo"/>
      <span class="name">{{user}}</span>
    </div>
    <a-menu :class="['avatar-menu']" slot="overlay" @click="changeUser">
      <a-menu-item key="upPwd">
        <a-icon type="user" />
        <span>修改密码</span>
      </a-menu-item>
      <a-menu-divider />
      <a-menu-item @click="logout">
        <a-icon style="margin-right: 8px;" type="poweroff" />
        <span>退出登录</span>
      </a-menu-item>

      <a-modal v-model="upUserData.show" title="修改密码" forceRender>
        <template slot="footer">
          <a-button key="back" @click="upUserData.show=false">
            关闭
          </a-button>
          <a-button key="submit" type="primary" :loading="upUserData.loading" @click="upUserPwdFunc">
            修改
          </a-button>
        </template>
        <a-form :form="upUserData.form" v-bind="upUserData.formItemLayout">
          <a-form-item label="密码">
            <a-input-password v-decorator="['pwd',{ rules: [{ required: true, message: '请输入账号' }] }]"/>
          </a-form-item>
        </a-form>
      </a-modal>
    </a-menu>
  </a-dropdown>
</template>

<script>
import {mapGetters} from 'vuex'
import {logout} from '@/services/user'
import userLogo from '@/assets/img/user.jpg'
import { upUserPwd } from '@/services/userSettings'


const formItemLayout = {
  labelCol: { span: 6 },
  wrapperCol: { span: 14 },
};

export default {
  name: 'HeaderAvatar',
  computed: {
    ...mapGetters('account', ['user']),
  },
  data() {
    return {
      userLogo,
      upUserData:{
        buffer:[],
        show:false,
        loading:false,
        formItemLayout,
        form: this.$form.createForm(this, { name: 'dynamic_rule' }),
      }
    }
  },
  methods: {
    logout() {
      logout()
      this.$router.push('/login')
    },
    changeUser({ key }){
      if(key == 'upPwd'){
        this.upUserData.show = true
      }
    },
    upUserPwdFunc(){
      this.upUserData.form.validateFields((err,values) => {
        if (!err) {
          var json = {
            pwd:values.pwd
          }
          upUserPwd(json).then(({data})=>{
            if(data.code == 20000){
              this.$message.info("修改成功")
              this.upUserData.show = false
            }
          })
        }
      })
    }
  },
}
</script>

<style lang="less">
  .header-avatar{
    display: inline-flex;
    .avatar, .name{
      align-self: center;
    }
    .avatar{
      margin-right: 8px;
    }
    .name{
      font-weight: 500;
    }
  }
  .avatar-menu{
    width: 150px;
  }

</style>
