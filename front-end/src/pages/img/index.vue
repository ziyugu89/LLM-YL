<template>
  <page-layout>
    <a-card>
      <a-row>
        <a-col :span="24" v-show="addUserData.show">
          <a-form
            :form="addUserData.form"
            @submit="onSubmit"
            v-bind="addUserData.formItemLayout"
          >
            <a-form-item :label="$t('label1')">
              <a-input
                v-decorator="[
                  'bingid',
                  { rules: [{ required: true, message: $t('message1') }] },
                ]"
              />
            </a-form-item>
            <a-form-item :label="$t('label2')">
              <a-input
                v-decorator="[
                  'name',
                  { rules: [{ required: true, message:  $t('message2')}] },
                ]"
              />
            </a-form-item>
            <a-form-item :label="$t('label3')">
              <a-radio-group
                v-decorator="['gender', { initialValue: '1' }]"
                style="width: 100%;"
              >
                <a-row>
                  <a-col :span="12">
                    <a-radio value="1">
                      {{$t('sex1')}}
                    </a-radio>
                    <a-radio value="2">
                      {{$t('sex2')}}
                    </a-radio>
                  </a-col>
                </a-row>
              </a-radio-group>
            </a-form-item>
            <a-form-item :label="$t('label4')">
              <a-input
                v-decorator="[
                  'age',
                  { rules: [{ required: true, message: $t('message3') }] },
                ]"
              />
            </a-form-item>
            <!-- <a-form-item :label="$t('label5')">
              <a-input
                v-decorator="[
                  'name',
                  { rules: [{ required: true, message: $t('message4') }] },
                ]"
              />
            </a-form-item> -->
            <a-form-item :label="$t ('label6')" >
              <a-textarea
                v-decorator="[
                  'text',
                  { rules: [{ required: true, message: $t('message5') }] },
                ]"
              />
            </a-form-item>
            <a-form-item style="padding-left: 20px;">
              <a-button
                :loading="addUserData.loading"
                style="margin-top: 24px;margin-left: 12.5%;"
                htmlType="submit"
                type="primary"
                >{{$t('button1')}}</a-button
              >
            </a-form-item>
          </a-form>
        </a-col>

        <a-col :span="24" v-show="addMessage.show">
          <a-form
            :form="addMessage.form"
            @submit="onSubmitForMessage"
            v-bind="addMessage.formItemLayout"
          >
            <a-form-item :label="$t('label1')">
              <a-input
                v-decorator="[
                  'bingid',
                  { rules: [{ required: true, message: $t('message1')}] },
                ]"
              />
            </a-form-item>
            <a-form-item :label="$t('label7')">
              <a-range-picker
                v-decorator="[
                  'day',
                  { rules: [{ required: true, message: $t('message6')}] },
                ]"
              />
            </a-form-item>
            <a-form-item :label="$t('label8')">
              <a-time-picker
                :default-open-value="moment('00:00:00', 'HH:mm:ss')"
                v-decorator="[
                  'time',
                  { rules: [{ required: true, message: $t('message7') }] },
                ]"
              />
            </a-form-item>
            <a-form-item :label="$t('label9')">
              <a-input
                v-decorator="[
                  'message',
                  { rules: [{ required: true, message: $t('message8') }] },
                ]"
              />
            </a-form-item>

            <a-form-item style="padding-left: 20px;">
              <a-button
                :loading="addMessage.loading"
                style="margin-top: 24px;margin-left: 12.5%;"
                htmlType="submit"
                type="primary"
                >{{$t('button1')}}</a-button
              >
            </a-form-item>
          </a-form>
        </a-col>

        <a-col :span="24" v-show="!addUserData.show && !addMessage.show">
          <div style="display: flex;justify-content: space-between;">
            <div>
              <a-button type="primary" @click="addUserData.show = true">
                {{$t('button2')}}
              </a-button>
              <a-button
                type="primary"
                @click="addMessage.show = true"
                style="margin-left: 5px"
              >
                {{$t('button3')}}
              </a-button>
            </div>

            <a-input-search
              :placeholder="$t('placeholder1')"
              style="width: 200px"
              @search="onSearch"
            />
          </div>
        </a-col>
        <a-col :span="24" v-show="!addUserData.show && !addMessage.show">
          <standard-table
            :columns="columns"
            :dataSource="newDataSource"
            :pagination="false"
            rowKey="user"
          >
          </standard-table>
        </a-col>
      </a-row>
    </a-card>
  </page-layout>
</template>

<script>
import PageLayout from "@/layouts/PageLayout";
import { addbingli, getbingli, setmessage } from "@/services/userSettings";
import StandardTable from "@/components/table/StandardTable";
import moment from "moment";

const getTimes = (l) => {
  if (l == 0 || l == null) {
    return "-";
  }

  l = l * 1000;
  var i = new Date(l);
  var o = i.getFullYear();
  var n =
    String(i.getMonth() + 1).length == 2
      ? i.getMonth() + 1
      : "0" + (i.getMonth() + 1);
  var j = String(i.getDate()).length == 2 ? i.getDate() : "0" + i.getDate();
  var k = String(i.getHours()).length == 2 ? i.getHours() : "0" + i.getHours();
  var p =
    String(i.getMinutes()).length == 2 ? i.getMinutes() : "0" + i.getMinutes();
  var m =
    String(i.getSeconds()).length == 2 ? i.getSeconds() : "0" + i.getSeconds();
  return o + "-" + n + "-" + j + " " + k + ":" + p + ":" + m;
};

export default {
  components: { PageLayout, StandardTable },
  i18n: require("./i18n"),
  data() {
    return {
      addUserData: {
        show: false,
        formItemLayout: {
          labelCol: { span: 3 },
          wrapperCol: { span: 21 },
        },
        loading: false,
        form: this.$form.createForm(this, { name: "dynamic_rule" }),
      },

      addMessage: {
        show: false,
        formItemLayout: {
          labelCol: { span: 3 },
          wrapperCol: { span: 21 },
        },
        loading: false,
        form: this.$form.createForm(this, { name: "dynamic_rule" }),
      },

      columns: [
        {
          title: this.$t('column1'),
          dataIndex: "pcode",
          customRender: (text, row) => text || row.bingid,
        },
        {
          title: this.$t('column2'),
          dataIndex: "name",
          // scopedSlots: { customRender: 'description' }
        },
        {
          title: this.$t('column3'),
          dataIndex: "time",
          customRender: (text) => getTimes(text),
        },
        {
          title: this.$t('column4'),
          dataIndex: "gender",
          customRender: (text) => (text == "1" ? "男" : "女"),
        },
        {
          title: this.$t('column5'),
          dataIndex: "age",
        },
        {
          title: this.$t('column6'),
          dataIndex: "text",
        },
      ],
      dataSource: [],
      newDataSource: [],
    };
  },
  authorize: {
    deleteRecord: "delete",
  },
  created() {
    this.getList();
    this.openFromRoute();
  },
  watch: {
    "$i18n.locale": {
      immediate: true,
      handler() {
        this.updateColumns();
      },
    },
    "$route.query.panel"() {
      this.openFromRoute();
    },
  },
  methods: {
    moment,
    getList() {
      getbingli().then((re) => {
        let { data } = re;
        this.newDataSource = this.dataSource = data.data.list;
      });
    },
    onSubmit(e) {
      e.preventDefault();
      this.addUserData.form.validateFields((err, values) => {
        if (!err) {
          this.addUserData.logging = true;
          addbingli(values)
            .then(() => {
              this.$message.success(this.$t('success'));
              // 重置表单
              this.addUserData.form.resetFields();
              // 恢复
              this.addUserData.show = false;
            })
            .finally(() => {
              this.addUserData.logging = false;
            });
        }
      });
    },
    onSearch(value) {
      const newArr = [...this.dataSource];
      this.newDataSource =
        value === ""
          ? this.dataSource
          : newArr.filter((d) => {
              if (d.bingid == value || d.pcode == value || d.name == value) {
                return true;
              } else {
                return false;
              }
            });
    },
    onSubmitForMessage(e) {
      e.preventDefault();
      this.addMessage.form.validateFields((err, values) => {
        if (!err) {
          // 创建一个空数组来存储区间内的所有日期
          const dateRange = [];
          // 使用一个循环来生成每个日期
          let currentDate = values.day[0].clone();
          while (currentDate <= values.day[1]) {
            dateRange.push(
              moment(
                currentDate.format(
                  "YYYY-MM-DD" + " " + values.time.format("HH:mm:ss")
                )
              ).unix()
            );
            currentDate.add(1, "days");
          }
          this.addMessage.logging = true;
          setmessage({ ...values, times: dateRange })
            .then(() => {
              this.$message.success(this.$t('success'));
              // 重置表单
              this.addMessage.form.resetFields();
              // 恢复
              this.addMessage.show = false;
            })
            .finally(() => {
              this.addMessage.logging = false;
            });
        }
      });
    },
        updateColumns() {
      this.columns = [
        {
          title: this.$t('column1'),
          dataIndex: "pcode",
          customRender: (text, row) => text || row.bingid,
        },
        {
          title: this.$t('column2'),
          dataIndex: "name",
        },

        {
          title: this.$t('column4'),
          dataIndex: "gender",
          customRender: (text) => (text == "1" ? "男" : "女"),
        },
        {
          title: this.$t('column5'),
          dataIndex: "age",
        },
        {
          title: this.$t('column6'),
          dataIndex: "text",
        },
                {
          title: this.$t('column3'),
          dataIndex: "time",
          customRender: (text) => this.getTimes(text),
        },
      ];
    },
        openFromRoute() {
      if (this.$route.query.panel === "remind") {
        this.addUserData.show = false;
        this.addMessage.show = true;
      }
    },
  },
};
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
