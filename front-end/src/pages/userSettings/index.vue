<template>
  <page-layout>
    <a-card>
      <div>
        <a-space class="operator">
          <a-button type="primary" @click="showAddUser">{{$t('button1')}}</a-button>
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
                  <a-col :span="12">
                    <a-checkbox value="3">{{$t('role1')}}</a-checkbox>
                  </a-col>
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
                  <a-col :span="12">
                    <a-checkbox value="3">{{$t('role1')}}</a-checkbox>
                  </a-col>
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
            <a key="del" style="margin-right: 8px" @click="handleDelete(text)">
              <a-icon type="delete"/>{{$t('button6')}}
            </a>
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
          title: this.$t('columns.account'),
          dataIndex: 'user'
        },
        {
          title: this.$t('columns.name'),
          dataIndex: 'name',
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
        page: this.page.num
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
    showAddUser() {
      this.addUserData.show = true;
    },
    addUserDataFunc() {
      this.addUserData.form.validateFields((err, values) => {
        if (!err) {
          addUser(values).then(({ data }) => {
            if (data.code == 20000) {
              this.$message.info(this.$t('success2'))
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
  @media screen and (max-width: 900px) {
    .fold {
      width: 100%;
    }
  }
</style>