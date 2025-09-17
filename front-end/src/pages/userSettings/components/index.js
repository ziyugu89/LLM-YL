const getTimes = (l) => {
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
}

const getStatus = (num) => {
  if (num == 1) {
    return '正常'
  } else {
    return '无法登录'
  }
}

export const columns = [
  {
    title: '账号',
    dataIndex: 'user'
  },
  {
    title: '用户名称',
    dataIndex: 'name',
    // scopedSlots: { customRender: 'description' }
  },
  {
    title: '最近登录时间',
    dataIndex: 'stime',
    customRender: (text) => getTimes(text)
  },
  {
    title: '权限',
    dataIndex: 'status',
    customRender: (text) => getStatus(text)
    // slots: { title: 'statusTitle' }
  },
  {
    title: '操作',
    scopedSlots: { customRender: 'action' }
  }
]

export const formItemLayout = {
  labelCol: { span: 6 },
  wrapperCol: { span: 14 },
};
export const formTailLayout = {
  labelCol: { span: 4 },
  wrapperCol: { span: 8, offset: 4 },
};