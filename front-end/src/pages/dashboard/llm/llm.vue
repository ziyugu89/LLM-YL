<template>
  <page-layout>
  <a-card class="chat-card" :body-style="{ padding: '16px' }">
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
          <div v-if="message.actions && message.actions.length" class="jump-actions">
            <button
              v-for="action in message.actions"
              :key="action.path + action.title"
              type="button"
              @click="openAction(action)"
            >{{ action.title }}</button>
          </div>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="agent-toggle">
        <a-switch v-model="useAgent" />
        <span title="先检索资料。打开后会继续查，并决定要打开哪个功能。">{{$t('useAgent')}}</span>
      </div>
      <div class="composer">
        <input
          v-model="newMessage"
          type="text"
          :placeholder="$t('text1')"
          @keyup.enter="sendMessage"
        />
        <button type="button" class="send-btn" @click="sendMessage">{{$t('button')}}</button>
      </div>
    </div>
  </div>
  </a-card>
  </page-layout>
</template>

<script>
import userpng from "@/assets/img/user.jpg";
import robotjpg from "@/assets/img/robot.jpg";
import PageLayout from "@/layouts/PageLayout";
import { llm } from "@/services/userSettings";
import { marked } from 'marked';

export default {
  name: 'llm',
  components: { PageLayout },
  i18n: require("./i18n"),
  data() {
    return {
      userpng,
      robotjpg,
      newMessage: "",
      useAgent: false,
      sending: false,
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
    openAction(action) {
      const allowed = ["/guide", "/hospital", "/img", "/imgbh", "/userSettings", "/dashboard"];
      if (!action || allowed.indexOf(action.path) === -1) return;
      this.$router.push({ path: action.path, query: action.query || {} });
    },
    sendMessage() {
      const question = this.newMessage.trim();
      if (question === "" || this.sending) return;
      this.sending = true;
      this.newMessage = "";
      this.messages.push({ text: question, isUser: true });
      this.messages.push({ text: this.$t('text3'), isUser: false });
      llm({
        query: question,
        use_agent: this.useAgent
      }).then(({ data }) => {
        this.messages.pop();
        if (data.code === 20000 && data.data && data.data.choices && data.data.choices.length > 0) {
          const messageContent = data.data.choices[0].message.content;
          const htmlContent = marked(messageContent);
          this.messages.push({
            text: htmlContent,
            isUser: false,
            isHtml: true,
            actions: (data.data && data.data.actions) || [],
          });
        } else {
          this.messages.push({ text: (data && data.data) || '查询失败', isUser: false });
        }
      }).catch((error) => {
        console.error('请求失败:', error);
        this.messages.pop();
        this.messages.push({ text: '请求失败，请稍后再试', isUser: false });
      }).finally(() => {
        this.sending = false;
      });
    },
  },
  created() {
    // 组件创建时更新消息数组
    this.updateMessages();
  },
};
</script>

<style scoped>
.chat-card {
  border-top: 3px solid #1e4636;
}

.chat-container {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 320px);
  min-height: 360px;
}

.chat-box {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 16px;
  border: 1px solid #e4ddd0;
  border-radius: 10px;
  padding: 16px;
  background: #f7f3ea;
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
  background: #1e4636;
  color: #f7f3ea;
}

.bot-message .content {
  background: #fffdf8;
  color: #1c1915;
  border: 1px solid #e4ddd0;
}

.jump-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.jump-actions button {
  padding: 4px 10px;
  border: 1px solid #1e4636;
  border-radius: 8px;
  background: #fffdf8;
  color: #1e4636;
  cursor: pointer;
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

.composer {
  display: flex;
  gap: 8px;
}

.composer input {
  flex: 1;
  padding: 10px 12px;
  border: 1px solid #e4ddd0;
  border-radius: 8px;
  background: #fffdf8;
  color: #1c1915;
}

.send-btn {
  padding: 10px 20px;
  background: #1e4636;
  color: #f7f3ea;
  border: 1px solid #1e4636;
  border-radius: 8px;
  cursor: pointer;
}

.send-btn:hover {
  background: #163628;
}
</style>
