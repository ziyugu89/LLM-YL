<template>
  <page-toggle-transition :disabled="true">
    <router-view />
  </page-toggle-transition>
</template>

<script>
import PageToggleTransition from '../components/transition/PageToggleTransition';
import {mapState} from 'vuex'

export default {
  name: 'BlankView',
  components: {PageToggleTransition},
  computed: {
    ...mapState('setting', ['multiPage', 'animate'])
  }
}
</script>

<style scoped>

</style>
