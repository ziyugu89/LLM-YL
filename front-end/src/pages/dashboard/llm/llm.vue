<template>
  <div class="chat-container">
    <div class="chat-box">
      <div
        v-for="(message, index) in messages"
        :key="index"
        class="message"
        :class="{
          'user-message': message.isUser,
          'bot-message': !message.isUser,
        }"
      >
        <div
          class="avatar"
          :class="{
            'user-avatar': message.isUser,
            'bot-avatar': !message.isUser,
          }"
        >
          <img v-if="message.isUser" :src="userpng" alt="User Avatar" />
          <img v-else :src="robotjpg" alt="Bot Avatar" />
        </div>
        <div class="content">
          <p v-if="!message.isHtml">{{ message.text }}</p>
          <div v-else v-html="message.text"></div>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="agent-toggle">
        <a-switch v-model="useAgent" />
        <span>{{$t('useAgent')}}</span>
      </div>
      <input
        v-model="newMessage"
        type="text"
        :placeholder="$t('text1')"
        @keyup.enter="sendMessage"
      />
      <button @click="sendMessage">{{$t('button')}}</button>
    </div>
  </div>
</template>

<script>
import userpng from "@/assets/img/user.jpg";
import robotjpg from "@/assets/img/robot.jpg";
import { llm } from "@/services/userSettings";
import { marked } from 'marked';

export default {
  name: 'llm',
  i18n: require("./i18n"),
  data() {
    return {
      userpng,
      robotjpg,
      newMessage: "",
      useAgent: false,
      messages: [
        { key: 'text2', isUser: false },
      ],
    };
  },
  watch: {
    // 监听语言变化
    '$i18n.locale': {
      immediate: true,
      handler() {
        this.updateMessages();
      }
    }
  },
  methods: {
    updateMessages() {
      this.messages.forEach(message => {
        if (message.key) {
          message.text = this.$t(message.key);
        }
      });
    },
    sendMessage() {
      if (this.newMessage.trim() === "") return;
      this.messages.push({ text: this.newMessage, isUser: true });

      this.messages.push({ key: 'text3', isUser: false });
      llm({
        query: this.newMessage,
        use_agent: this.useAgent  // 添加Agent参数
      }).then(({ data }) => {
        // 移除数组最后一个
        this.messages.pop();
        if (data.code === 20000 && data.data && data.data.choices && data.data.choices.length > 0) {
          let messageContent = data.data.choices[0].message.content;
          // 渲染 Markdown 为 HTML
          const htmlContent = marked(messageContent);
          // 使用 v-html 渲染
          this.messages.push({ text: htmlContent, isUser: false, isHtml: true });
        } else {
          this.messages.push({ text: '查询失败', isUser: false });
        }
        console.log('当前消息列表:', this.messages); // 打印消息列表
      }).catch((error) => {
        console.error('请求失败:', error);
        this.messages.push({ text: '请求失败，请稍后再试', isUser: false });
      });
      this.newMessage = "";
    },
  },
  created() {
    // 组件创建时更新消息数组
    this.updateMessages();
  },
};
</script>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding: 20px;
}

.chat-box {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 20px;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
  padding: 10px;
  background-color: #f9f9f9;
}

.message {
  display: flex;
  margin-bottom: 15px;
}

.user-message {
  flex-direction: row-reverse;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  margin: 0 10px;
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.content {
  max-width: 70%;
  padding: 10px;
  border-radius: 8px;
}

.user-message .content {
  background-color: #1890ff;
  color: white;
}

.bot-message .content {
  background-color: #f0f0f0;
  color: #333;
}

.input-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.agent-toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

input {
  flex: 1;
  padding: 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
}

button {
  padding: 10px 20px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

button:hover {
  background-color: #40a9ff;
}
</style>
