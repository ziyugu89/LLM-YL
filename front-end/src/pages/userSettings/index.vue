<template>
  <page-layout>
    <a-card>
      <div>
        <div class="desk-intro">
          <strong>账号管理</strong>
          <span>管理员可以新建、查询、修改和注销账号。患者会自动分配 8 位就诊编号。医生只能查询患者，不能注销账号。</span>
        </div>
        <a-space class="operator">
          <a-button type="primary" @click="showAddUser">{{$t('button1')}}</a-button>
          <a-input-search
            v-model="keyword"
            placeholder="按姓名、账号或就诊编号查询"
            enter-button="查询"
            style="width: 320px"
            @search="searchUsers"
          />
        </a-space>
        <a-modal v-model="addUserData.show" :title="$t('title1')">
          <template slot="footer">
            <a-button key="back" @click="addUserData.show=false">{{$t('button2')}}</a-button>
            <a-button key="submit" type="primary" :loading="addUserData.loading" @click="addUserDataFunc">{{$t('button3')}}</a-button>
          </template>
          <a-form :form="addUserData.form" v-bind="addUserData.formItemLayout">
            <a-form-item :label="$t('label1')">
              <a-input
                v-decorator="[ 'user', { rules: [{ required: true, message: $t('message1') }] }]"
              />
            </a-form-item>
            <a-form-item :label="$t('label2')">
              <a-input-password
                v-decorator="[ 'pwd', { rules: [{ required: true, message: $t('message2') }] }]"
              />
            </a-form-item>
            <a-form-item :label="$t('label3')">
              <a-input
                v-decorator="[ 'name', { rules: [{ required: true, message: $t('message3') }] }]"
              />
            </a-form-item>
            <a-form-item :label="$t('label4')">
              <a-checkbox-group
                v-decorator="['roles', { initialValue: ['3'] }]"
                style="width: 100%;"
              >
                <a-row>
                  <a-col :span="8"><a-checkbox value="2">患者</a-checkbox></a-col>
                  <a-col :span="8"><a-checkbox value="3">医生</a-checkbox></a-col>
                  <a-col :span="8"><a-checkbox value="1">管理员</a-checkbox></a-col>
                </a-row>
              </a-checkbox-group>
            </a-form-item>
          </a-form>
        </a-modal>

        <a-modal v-model="upUserData.show" :title="$t('title2')">
          <template slot="footer">
            <a-button key="back" @click="upUserData.show=false">{{$t('button2')}}</a-button>
            <a-button key="submit" type="primary" :loading="upUserData.loading" @click="upUserDataFunc">{{$t('button4')}}</a-button>
          </template>
          <a-form :form="upUserData.form" v-bind="upUserData.formItemLayout">
            <a-form-item :label="$t('label1')">
              <a-input
                v-decorator="[ 'user', { rules: [{ required: true, message: $t('message1') }] }]"
                disabled
              />
            </a-form-item>
            <a-form-item :label="$t('label2')">
              <a-input-password v-decorator="['pwd']"/>
            </a-form-item>
            <a-form-item :label="$t('label3')">
              <a-input
                v-decorator="[ 'name', { rules: [{ required: true, message: $t('message3') }] }]"
              />
            </a-form-item>
            <a-form-item :label="$t('label4')">
              <a-checkbox-group
                v-decorator="['roles', { initialValue: ['3'] }]"
                style="width: 100%;"
              >
                <a-row>
                  <a-col :span="8"><a-checkbox value="2">患者</a-checkbox></a-col>
                  <a-col :span="8"><a-checkbox value="3">医生</a-checkbox></a-col>
                  <a-col :span="8"><a-checkbox value="1">管理员</a-checkbox></a-col>
                </a-row>
              </a-checkbox-group>
            </a-form-item>
          </a-form>
        </a-modal>

        <standard-table
          :columns="columns"
          :dataSource="dataSource"
          @change="onChange"
          :pagination="false"
          rowKey="user"
        >
          <template v-slot:action="{text}">
            <a key="edit" style="margin-right: 8px" @click="handleEdit(text)">
              <a-icon type="edit"/>{{$t('button5')}}
            </a>
            <a v-if="text.status == 1" key="del" @click="handleDelete(text)">
              <a-icon type="stop"/>{{$t('button6')}}
            </a>
            <span v-else>已注销</span>
          </template>
          <template v-slot:statusTitle>
            <a-icon @click.native="onStatusTitleClick" type="info-circle" />
          </template>
        </standard-table>
        <a-pagination
          @change="fetchData"
          style="margin-top:20px;"
          :pageSize="20"
          v-model="page.num"
          :total="page.total"
        />
      </div>
    </a-card>
  </page-layout>
</template>

<script>
import StandardTable from '@/components/table/StandardTable'
import PageLayout from '@/layouts/PageLayout'
import { getList, addUser, upUser, delUser } from '@/services/userSettings'

export default {
  components: { StandardTable, PageLayout },
  i18n: require("./i18n"),
  data () {
    return {
      columns: this.initColumns(),
      dataSource: [],
      page: {
        total: 0,
        num: 1
      },
      keyword: "",
      addUserData: {
        show: false,
        loading: false,
        formItemLayout: { labelCol: { span: 6 }, wrapperCol: { span: 14 } },
        formTailLayout: { labelCol: { span: 4 }, wrapperCol: { span: 8, offset: 4 } },
        form: this.$form.createForm(this, { name: 'dynamic_rule' }),
      },
      upUserData: {
        buffer: [],
        show: false,
        loading: false,
        formItemLayout: { labelCol: { span: 6 }, wrapperCol: { span: 14 } },
        formTailLayout: { labelCol: { span: 4 }, wrapperCol: { span: 8, offset: 4 } },
        form: this.$form.createForm(this, { name: 'dynamic_rule' }),
      }
    }
  },
  authorize: {
    deleteRecord: 'delete'
  },
  created() {
    this.fetchData()
  },
  methods: {
    initColumns() {
      return [
        {
          title: this.$t('columns.code'),
          dataIndex: 'pcode',
          customRender: (text) => text || '—'
        },
        {
          title: this.$t('columns.account'),
          dataIndex: 'user'
        },
        {
          title: this.$t('columns.name'),
          dataIndex: 'name',
        },
        {
          title: this.$t('columns.role'),
          dataIndex: 'roleText',
        },
        {
          title: this.$t('columns.lastLogin'),
          dataIndex: 'stime',
          customRender: (text) => this.getTimes(text)
        },
        {
          title: this.$t('columns.permission'),
          dataIndex: 'status',
          customRender: (text) => this.getStatus(text)
        },
        {
          title: this.$t('columns.action'),
          scopedSlots: { customRender: 'action' }
        }
      ];
    },
    getTimes(l) {
      if (l == 0 || l == null) {
        return '-';
      }
      l = l * 1000;
      var i = new Date(l);
      var o = i.getFullYear();
      var n = String(i.getMonth() + 1).length == 2 ? i.getMonth() + 1 : '0' + (i.getMonth() + 1);
      var j = String(i.getDate()).length == 2 ? i.getDate() : '0' + i.getDate();
      var k = String(i.getHours()).length == 2 ? i.getHours() : '0' + i.getHours();
      var p = String(i.getMinutes()).length == 2 ? i.getMinutes() : '0' + i.getMinutes();
      var m = String(i.getSeconds()).length == 2 ? i.getSeconds() : '0' + i.getSeconds();
      return o + '-' + n + '-' + j + ' ' + k + ':' + p + ':' + m;
    },
    getStatus(num) {
      if (num == 1) {
        return this.$t('status.normal')
      } else {
        return this.$t('status.unlogin')
      }
    },
    fetchData() {
      getList({
        page: this.page.num,
        keyword: this.keyword
      }).then(re => {
        let { data } = re;
        this.dataSource = data.data.list;
        this.page.total = data.data.total;
      })
    },
    onStatusTitleClick() {
      this.$message.info(this.$t('message4'))
    },
    onChange() {
      this.$message.info(this.$t('message5'))
    },
    handleEdit(text) {
      this.upUserData.show = true;
      this.$nextTick(() => {
        this.upUserData.buffer = text;
        this.upUserData.form.setFieldsValue({
          name: text.name,
          roles: text.roles.split(","),
          user: text.user,
          pwd: ''
        })
      })
    },
    handleDelete(text) {
      this.$confirm({
        title: this.$t('title3'),
        content: this.$t('message6'),
        onOk: () => {
          delUser({ id: text.id }).then(({ data }) => {
            if (data.code == 20000) {
              this.$message.info(this.$t('success1'))
              this.fetchData()
            }
          })
        },
        onCancel() {},
      });
    },
    searchUsers() {
      this.page.num = 1
      this.fetchData()
    },
    showAddUser() {
      this.addUserData.show = true;
    },
    addUserDataFunc() {
      this.addUserData.form.validateFields((err, values) => {
        if (!err) {
          addUser(values).then(({ data }) => {
            if (data.code == 20000) {
              const pcode = data.data && data.data.pcode
              this.$message.info(pcode ? `创建成功，就诊编号 ${pcode}` : this.$t('success2'))
              this.addUserData.show = false;
              this.fetchData()
            }
          })
        }
      });
    },
    upUserDataFunc() {
      this.upUserData.form.validateFields((err, values) => {
        if (!err) {
          var json = {
            name: values.name,
            roles: values.roles,
            user: values.user,
            pwd: values.pwd,
            id: this.upUserData.buffer.id
          }
          upUser(json).then(({ data }) => {
            if (data.code == 20000) {
              this.$message.info(this.$t('success3'))
              this.upUserData.show = false;
              this.fetchData()
            }
          })
        }
      });
    }
  },
  watch: {
    '$i18n.locale': function() {
      this.columns = this.initColumns();
    }
  }
}
</script>

<style lang="less" scoped>
  .search {
    margin-bottom: 54px;
  }
  .fold {
    width: calc(100% - 216px);
    display: inline-block;
  }
  .operator {
    margin-bottom: 18px;
  }
  .desk-intro {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 16px;
    padding: 14px 16px;
    background: #f4f8f6;
    border-radius: 8px;
    line-height: 1.7;
  }
  @media screen and (max-width: 900px) {
    .fold {
      width: 100%;
    }
  }
</style>